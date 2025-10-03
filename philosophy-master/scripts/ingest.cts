// docker run -p 8000:8000 -v ./chroma-data:/data chromadb/chroma
// npx ts-node --project tsconfig.cjs.json scripts/ingest.cts

const { ChromaClient } = require("chromadb-client");
const { pipeline } = require("@xenova/transformers");
const mammoth = require("mammoth");
const pdf = require("pdf-parse");
const fs = require("fs/promises");
const path = require("path");

import { CloudClient } from "chromadb";

const client = new CloudClient({
	apiKey: "ck-49KKmM6dx4zdhgKX6wRcFkvemQRQUaqErLt6pxkox8FK",
	tenant: "8b9f17b6-e2ac-421e-ad4c-95e41fe32e1b",
	database: "test",
});

// --- CẤU HÌNH ---
const DOCUMENTS_PATH = path.resolve(process.cwd(), "documents");
const CHROMA_URL = "http://localhost:8000";
const COLLECTION_NAME = "philosophy_docs";
const CHUNK_SIZE = 500;
const CHUNK_OVERLAP = 50;

// --- LỚP SINGLETON ---
class EmbeddingPipelineSingleton {
	static task = "feature-extraction";
	static model = "Xenova/all-MiniLM-L6-v2";
	static instance: any = null;

	static async getInstance(progress_callback?: (progress: any) => void) {
		if (this.instance === null) {
			console.log("Loading embedding model for the first time...");
			this.instance = await pipeline(this.task, this.model, {
				progress_callback,
			});
			console.log("Embedding model loaded successfully.");
		}
		return this.instance;
	}
}

// --- HÀM TIỆN ÍCH (SỬ DỤNG PDF-PARSE) ---
async function extractTextFromBuffer(buffer: Buffer, fileType: "pdf" | "docx"): Promise<string> {
	if (fileType === "pdf") {
		const data = await pdf(buffer);
		return data.text;
	} else if (fileType === "docx") {
		const { value } = await mammoth.extractRawText({ buffer });
		return value;
	}
	throw new Error("Unsupported file type");
}

function chunkText(text: string): string[] {
	const chunks: string[] = [];
	for (let i = 0; i < text.length; i += CHUNK_SIZE - CHUNK_OVERLAP) {
		chunks.push(text.substring(i, i + CHUNK_SIZE));
	}
	return chunks;
}

// --- KẾT THÚC PHẦN CODE BỊ THIẾU ---

// --- HÀM CHÍNH (PHIÊN BẢN SIÊU THÔNG MINH) ---
async function ingestData() {
	// const client = new ChromaClient({ path: CHROMA_URL });
	console.log("Connecting to ChromaDB and preparing collection...");
	const collection = await client.getOrCreateCollection({
		name: COLLECTION_NAME,
		metadata: { "hnsw:space": "cosine" },
		embeddingFunction: null,
	});
	console.log(`Collection '${COLLECTION_NAME}' is ready.`);
	console.log("Fetching metadata of processed files from database...");
	const existingItems = await collection.get({ include: ["metadatas"] });
	const processedFiles = new Set(
		existingItems.metadatas.map((meta: any) => meta?.source).filter(Boolean)
	);
	console.log(`Found ${processedFiles.size} already processed files.`);
	const currentFiles = await fs.readdir(DOCUMENTS_PATH);
	// <<-- SỬA LỖI: Thêm kiểu 'string' cho file -->>
	const filesToProcess = currentFiles.filter((file: string) => !processedFiles.has(file));
	if (filesToProcess.length === 0) {
		console.log("No new files to process. Database is up to date.");
		return;
	}
	console.log(`Found ${filesToProcess.length} new files to process:`, filesToProcess);
	console.log("Starting ingestion for new files...");
	const extractor = await EmbeddingPipelineSingleton.getInstance((progress: any) => {
		console.log(`Loading model... ${progress.file} (${Math.round(progress.progress)}%)`);
	});
	let totalChunks = 0;
	for (const file of filesToProcess) {
		const filePath = path.join(DOCUMENTS_PATH, file);
		const fileExtension = path.extname(file).toLowerCase();
		if (fileExtension !== ".pdf" && fileExtension !== ".docx") {
			console.log(`Skipping unsupported file: ${file}`);
			continue;
		}
		console.log(`Processing new file: ${file}...`);
		const buffer = await fs.readFile(filePath);
		const text = await extractTextFromBuffer(buffer, fileExtension === ".pdf" ? "pdf" : "docx");
		const chunks = chunkText(text);
		console.log(`  - Extracted text, creating ${chunks.length} chunks.`);
		if (chunks.length > 0) {
			const embeddings: number[][] = [];
			for (const chunk of chunks) {
				const embedding = await extractor(chunk, { pooling: "mean", normalize: true });
				embeddings.push(Array.from(embedding.data) as number[]);
			}
			// <<-- SỬA LỖI: Thêm kiểu 'any' và 'number' cho _ và i -->>
			const ids = chunks.map((_: any, i: number) => `${file}-chunk-${i}`);
			const metadatas = chunks.map(() => ({ source: file }));
			await collection.add({
				ids: ids,
				embeddings: embeddings,
				metadatas: metadatas,
				documents: chunks,
			});
			totalChunks += chunks.length;
			console.log(`  - Added ${chunks.length} chunks for '${file}' to ChromaDB.`);
		}
	}
	console.log("---");
	console.log(`Incremental update complete! Total new chunks added: ${totalChunks}`);
}

ingestData().catch(console.error);
