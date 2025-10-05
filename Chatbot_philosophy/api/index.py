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

@app.route('/', methods=['GET'])
def home():
    """Endpoint để kiểm tra API có hoạt động không."""
    return "Chatbot API with custom logic is up and running!"

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