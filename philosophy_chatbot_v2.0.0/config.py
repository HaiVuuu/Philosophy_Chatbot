"""
File cấu hình chung cho hệ thống chatbot triết học
"""

import os
from pathlib import Path

# Đường dẫn cơ bản
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
LOG_DIR = BASE_DIR / "logs"

# Tạo thư mục nếu chưa tồn tại
for dir_path in [DATA_DIR, RAW_DATA_DIR, VECTOR_DB_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Danh sách các trường phái triết học
PHILOSOPHY_SCHOOLS = {
    "stoicism": {
        "name": "Stoicism (Khắc kỷ)",
        "description": "Triết học về sự kiểm soát cảm xúc và chấp nhận số phận",
        "color": "#2E7D32"
    },
    "nihilism": {
        "name": "Nihilism (Hư vô)",
        "description": "Triết học phủ nhận ý nghĩa và giá trị tuyệt đối",
        "color": "#424242"
    },
    "phenomenology": {
        "name": "Phenomenology (Hiện tượng học)",
        "description": "Nghiên cứu về ý thức và trải nghiệm trực tiếp",
        "color": "#1565C0"
    },
    "voluntarism": {
        "name": "Voluntarism (Duy ý chí)",
        "description": "Triết học đặt ý chí làm nền tảng của thực tại",
        "color": "#D84315"
    },
    "marxism": {
        "name": "Marxism (Chủ nghĩa Marx)",
        "description": "Triết học về đấu tranh giai cấp và biến đổi xã hội",
        "color": "#B71C1C"
    },
    "existentialism": {
        "name": "Existentialism (Hiện sinh)",
        "description": "Triết học về tự do, lựa chọn và trách nhiệm cá nhân",
        "color": "#4A148C"
    }
}

# Cấu hình cho embeddings và vector database
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 250  # Số token mỗi chunk
CHUNK_OVERLAP = 50  # Số token overlap giữa các chunk
TOP_K_RETRIEVAL = 5  # Số lượng đoạn văn liên quan cần lấy

# Cấu hình cho LLM
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # Nâng cấp lên Llama 3 8B
MAX_LENGTH = 1024  # Tăng độ dài tối đa cho response
TEMPERATURE = 0.6  # Điều chỉnh nhiệt độ cho Llama 3

# Cấu hình Socratic prompting
SOCRATIC_SYSTEM_PROMPT = """
Bạn là một triết gia {school} sử dụng phương pháp Socrates.
Khi trả lời:
1. Giải thích ngắn gọn dựa trên tài liệu được cung cấp
2. Đặt 1-2 câu hỏi phản tư để dẫn dắt người học suy nghĩ sâu hơn
3. Không đưa ra câu trả lời tuyệt đối, mà khuyến khích tư duy phê phán
4. Nếu câu hỏi nằm ngoài phạm vi tài liệu, từ chối một cách lịch sự

Tài liệu tham khảo:
{context}

Câu hỏi của người dùng: {question}

Hãy trả lời theo phong cách Socrates:
"""

# Cấu hình đánh giá
EVALUATION_QUESTIONS = {
    "stoicism": [
        "Làm thế nào để kiểm soát cảm xúc?",
        "Ý nghĩa của số phận là gì?",
        "Đức hạnh trong triết học khắc kỷ?"
    ],
    "nihilism": [
        "Cuộc sống có ý nghĩa không?",
        "Nietzsche nói gì về Thượng đế?",
        "Hư vô chủ nghĩa là gì?"
    ],
    "phenomenology": [
        "Ý thức là gì?",
        "Husserl và khái niệm hiện tượng?",
        "Trải nghiệm trực tiếp nghĩa là gì?"
    ],
    "voluntarism": [
        "Ý chí con người có tự do không?",
        "Schopenhauer về ý chí?",
        "Mối quan hệ giữa ý chí và hành động?"
    ],
    "marxism": [
        "Đấu tranh giai cấp là gì?",
        "Giá trị thặng dư trong tư bản?",
        "Biện chứng duy vật?"
    ],
    "existentialism": [
        "Tự do và trách nhiệm?",
        "Sartre về sự hiện hữu?",
        "Lo âu trong hiện sinh?"
    ]
}

# Cấu hình logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"