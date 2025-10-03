// npx ts-node --project tsconfig.cjs.json server.cts

const express = require("express");
const cors = require("cors");
import { Request, Response } from "express";

const { ChromaClient } = require("chromadb-client");
const { pipeline } = require("@xenova/transformers");
const { GoogleGenerativeAI } = require("@google/generative-ai");

require("dotenv").config({ path: ".env.local" });

// --- CÁC INTERFACE ĐỊNH NGHĨA KIỂU DỮ LIỆU ---
interface Philosopher {
	id: string;
	name: string;
	systemPrompt: string;
}
interface Message {
	sender: "user" | "model";
	text: string;
}
interface ChatRequestBody {
	query: string;
	philosopher: Philosopher;
	chatHistory: Message[];
}

// --- CẤU HÌNH ---
const PORT = 3001;
const GEMINI_API_KEY = process.env.VITE_GEMINI_API_KEY;
const CHROMA_URL = "http://localhost:8000";
const COLLECTION_NAME = "philosophy_docs";

if (!GEMINI_API_KEY) {
	throw new Error(
		"VITE_GEMINI_API_KEY not found in environment variables. Please check your .env.local file."
	);
}

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
const client = new ChromaClient({ path: CHROMA_URL });

// --- SINGLETON CHO MODEL EMBEDDING ---
class EmbeddingPipelineSingleton {
	static task = "feature-extraction";
	static model = "Xenova/all-MiniLM-L6-v2";
	static instance: any = null;

	static async getInstance() {
		if (this.instance === null) {
			console.log("Loading local embedding model for the first time on server...");
			this.instance = await pipeline(this.task, this.model, { quantized: true });
			console.log("Local embedding model loaded successfully on server.");
		}
		return this.instance;
	}
}

// --- KHỞI TẠO SERVER API ---
const app = express();
app.use(cors());
app.use(express.json());

// --- ENDPOINT /api/chat ĐÃ NÂNG CẤP LÊN STREAMING ---
app.post("/api/chat", async (req: Request<{}, {}, ChatRequestBody>, res: Response) => {
	try {
		// 1. Thiết lập headers cho Server-Sent Events (SSE) / Streaming
		res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
		res.setHeader("Cache-Control", "no-cache");
		res.setHeader("Connection", "keep-alive");
		res.flushHeaders(); // Gửi headers ngay lập tức để client biết kết nối thành công

		const { query, philosopher, chatHistory } = req.body;
		console.log(`Received streaming query for ${philosopher.name}: "${query}"`);

		// 2. Thực hiện phần RAG (lấy context). Phần này là blocking (phải chờ).
		const collection = await client.getCollection({ name: COLLECTION_NAME });
		const extractor = await EmbeddingPipelineSingleton.getInstance();
		const queryEmbedding = await extractor(query, { pooling: "mean", normalize: true });

		const results = await collection.query({
			queryEmbeddings: [Array.from(queryEmbedding.data)],
			nResults: 3,
		});

		const context =
			results.documents[0].length > 0
				? results.documents[0]
						.map(
							(doc: string | null, i: number) =>
								`Trích đoạn ${i + 1} (từ file '${results.metadatas[0][i]?.source || "unknown"}'):\n"${doc || ""}"`
						)
						.join("\n\n---\n")
				: "Không tìm thấy thông tin liên quan trong tài liệu.";

		const historyString = chatHistory
			.map((msg) => `${msg.sender === "user" ? "Người dùng" : "Model"}: ${msg.text}`)
			.join("\n");

		const augmentedPrompt = `
<System Instruction>
Bạn là nhà triết học ${philosopher.name}. Hãy nhập vai và trả lời bằng giọng văn, tư tưởng và phong cách của ông.
${philosopher.systemPrompt}
</System Instruction>

**BỐI CẢNH (CONTEXT):**
${context}

**LỊCH SỬ TRÒ CHUYỆN (CHAT HISTORY):**
${historyString}

**CÂU HỎI HIỆN TẠI TỪ NGƯỜỜI DÙNG (CURRENT QUESTION):**
${query}

**NHIỆM VỤ (TASK):**
Với vai trò là ${philosopher.name}, hãy trả lời CÂU HỎI HIỆN TẠI dựa trên BỐI CẢNH.
`;

		// 3. Gọi Gemini và bắt đầu stream kết quả
		const model = genAI.getGenerativeModel({ model: "gemini-2.5-pro" });
		const resultStream = await model.generateContentStream(augmentedPrompt);

		// 4. Lặp qua từng chunk dữ liệu và gửi về client
		for await (const chunk of resultStream.stream) {
			const chunkText = chunk.text();
			// Không cần 'data:' prefix, gửi thẳng text
			res.write(chunkText);
		}

		// 5. Kết thúc response khi stream hoàn tất
		console.log("Stream finished for the request.");
		res.end();
	} catch (error) {
		console.error("Error in /api/chat streaming endpoint:", error);
		// Nếu có lỗi, ghi log và kết thúc response để client không bị treo
		res.write("\n\n[ERROR]: Đã có lỗi xảy ra phía máy chủ.");
		res.end();
	}
});

app.listen(PORT, () => {
	console.log(`Backend server is running at http://localhost:${PORT}`);
	// Tải sẵn model embedding khi server khởi động để các request sau nhanh hơn
	EmbeddingPipelineSingleton.getInstance();
});
