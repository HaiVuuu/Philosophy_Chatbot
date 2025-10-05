import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- Khởi tạo ứng dụng Flask ---
app = Flask(__name__)
CORS(app) # Cho phép yêu cầu từ mọi nguồn gốc

# --- Biến toàn cục để lưu trữ các đối tượng LangChain ---
llm = None
retriever = None
initialization_error = None

def initialize_chatbot():
    """
    Hàm này khởi tạo mô hình và retriever.
    Nó sẽ chỉ chạy một lần khi serverless function khởi động.
    """
    global llm, retriever, initialization_error
    
    try:
        # 1. Lấy API key từ biến môi trường của Vercel
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            raise ValueError("Biến môi trường GOOGLE_API_KEY chưa được thiết lập.")

        # 2. Khởi tạo mô hình LLM (dựa trên file ipynb của bạn)
        # chatbot_configs
        temperature = 0.7
        top_p = 0.9
        top_k = 40
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k
        )

        # 3. Khởi tạo mô hình embeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 4. Tải FAISS index đã được tạo sẵn
        faiss_index_dir = os.path.join(os.path.dirname(__file__), '..', 'faiss_index')
        vector_store = FAISS.load_local(
            faiss_index_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )

        # 5. Tạo retriever với cấu hình chính xác như trong notebook
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5} # Lấy 5 tài liệu liên quan nhất
        )

        print("✅ Khởi tạo Chatbot với cấu hình tùy chỉnh thành công!")

    except Exception as e:
        initialization_error = str(e)
        print(f"❌ Lỗi nghiêm trọng khi khởi tạo: {initialization_error}")

# Chạy hàm khởi tạo ngay khi ứng dụng bắt đầu
initialize_chatbot()

# --- Định nghĩa các Route (API Endpoints) ---


# Biến HTML_TEMPLATE chứa giao diện chatbot
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"vi\">
<head>
    <title>Chatbot Triết Học</title>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f6fa; margin: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); padding: 32px; }
        h1 { color: #4a90e2; text-align: center; }
        .chatbox { min-height: 300px; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #fafbfc; }
        .message { margin: 12px 0; padding: 12px 18px; border-radius: 18px; max-width: 80%; word-break: break-word; }
        .user { background: #d0e7ff; text-align: right; margin-left: auto; }
        .bot { background: #e0f7fa; text-align: left; margin-right: auto; }
        .input-area { display: flex; gap: 10px; }
        .question { flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 18px; font-size: 15px; }
        .send-btn { padding: 12px 24px; background: #4a90e2; color: #fff; border: none; border-radius: 18px; cursor: pointer; font-size: 15px; }
        .send-btn:hover { background: #357abd; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Chatbot Triết Học</h1>
        <div class=\"chatbox\" id=\"chatbox\"></div>
        <div class=\"input-area\">
            <input type=\"text\" class=\"question\" id=\"question\" placeholder=\"Nhập câu hỏi triết học...\">
            <button class=\"send-btn\" id=\"sendBtn\">Gửi</button>
        </div>
    </div>
    <script>
    const chatbox = document.getElementById('chatbox');
    const questionInput = document.getElementById('question');
    const sendBtn = document.getElementById('sendBtn');
    let conversation = [];
    function addMessage(content, sender) {
        const msg = document.createElement('div');
        msg.className = 'message ' + sender;
        msg.innerHTML = content.replace(/\n/g, '<br>');
        chatbox.appendChild(msg);
        chatbox.scrollTop = chatbox.scrollHeight;
    }
    sendBtn.onclick = function() {
        const question = questionInput.value.trim();
        if (!question) return;
        addMessage(question, 'user');
        questionInput.value = '';
        addMessage('Đang suy nghĩ...', 'bot');
        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        })
        .then(res => res.json())
        .then(data => {
            chatbox.querySelector('.bot:last-child').remove();
            if (data.answer) addMessage(data.answer, 'bot');
            else addMessage('Lỗi: ' + (data.error || 'Không nhận được phản hồi'), 'bot');
        })
        .catch(() => {
            chatbox.querySelector('.bot:last-child').remove();
            addMessage('Lỗi kết nối server!', 'bot');
        });
    };
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendBtn.click();
    });
    </script>
</body>
</html>
"""

from flask import render_template_string

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask', methods=['POST'])
def ask_question():
    """Endpoint chính để nhận và trả lời câu hỏi."""
    # Kiểm tra lỗi trong quá trình khởi tạo
    if initialization_error:
        return jsonify({"error": f"Dịch vụ không khả dụng do lỗi cấu hình: {initialization_error}"}), 500
    
    if not retriever or not llm:
         return jsonify({"error": "Retriever hoặc LLM chưa được khởi tạo."}), 500

    # Lấy dữ liệu JSON từ yêu cầu
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Dữ liệu không hợp lệ. Vui lòng cung cấp 'question'."}), 400

    question = data['question']

    try:
        # --- Tái tạo lại logic xử lý từ file .ipynb ---
        
        # 1. Lấy các tài liệu liên quan bằng retriever
        relevant_docs = retriever.invoke(question)
        
        # 2. Tạo context bằng cách nối nội dung các tài liệu
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        # 3. Xây dựng FINAL PROMPT chính xác như trong file của bạn
        final_prompt = f"""
        Bạn là một trợ lý AI, nhiệm vụ của bạn là cung cấp câu trả lời chính xác và chi tiết dựa trên bối cảnh được cung cấp.
        Hãy phân tích kỹ bối cảnh và câu hỏi của người dùng để đưa ra câu trả lời đầy đủ, mạch lạc và bằng tiếng Việt.
        Không sử dụng thông tin bên ngoài, chỉ dựa vào văn bản dưới đây.

        Bối cảnh:
        ---
        {context}
        ---

        Dựa vào bối cảnh trên, hãy trả lời câu hỏi sau: "{question}"
        Nếu bối cảnh không chứa thông tin để trả lời, hãy nói: "Tôi xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi này trong tài liệu."
        Đảm bảo câu trả lời của bạn được trình bày một cách tự nhiên và hữu ích, như thể bạn là một chuyên gia về chủ đề này.
        """
        
        # 4. Gọi LLM với prompt cuối cùng
        answer = llm.invoke(final_prompt)
        
        # 5. Trả về câu trả lời
        return jsonify({"answer": answer.content})
        
    except Exception as e:
        print(f"Lỗi khi xử lý yêu cầu: {e}")
        return jsonify({"error": "Đã xảy ra lỗi khi xử lý câu hỏi của bạn."}), 500