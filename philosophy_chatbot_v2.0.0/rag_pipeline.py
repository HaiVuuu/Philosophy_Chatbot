"""
RAG Pipeline cho hệ thống chatbot triết học
Kết hợp retrieval từ vector database với generation từ LLM
"""

import logging
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig
)
from sentence_transformers import SentenceTransformer

from config import (
    VECTOR_DB_DIR, PHILOSOPHY_SCHOOLS,
    EMBEDDING_MODEL, TOP_K_RETRIEVAL,
    LLM_MODEL, MAX_LENGTH, TEMPERATURE
)
from data_preprocessing import PhilosophyDataProcessor

# Tải các biến môi trường từ file .env
load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Pipeline RAG (Retrieval-Augmented Generation) cho chatbot triết học
    """

    def __init__(self, school: str, use_gpu: bool = False):
        """
        Khởi tạo RAG Pipeline cho một trường phái triết học
        
        Args:
            school: Tên trường phái (vd: 'stoicism', 'nihilism',...)
            use_gpu: Sử dụng GPU nếu có
        """
        self.school = school
        self.school_info = PHILOSOPHY_SCHOOLS.get(school, {})
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"

        logger.info(f"[{school}] Khởi tạo RAG Pipeline trên {self.device}")

        # Khởi tạo retriever (vector database)
        self.retriever = PhilosophyDataProcessor(school)
        self._load_retriever()

        # Khởi tạo generator (LLM)
        self.model = None
        self.tokenizer = None
        self.generator = None
        self._load_generator()

        # Cache cho conversation history
        self.conversation_history = []

    def _load_retriever(self):
        """
        Nạp vector database cho retrieval
        """
        success = self.retriever.load_database()
        if not success:
            logger.warning(f"[{self.school}] Không thể nạp database, đang tạo mới...")
            self.retriever.process_data()

    def _load_generator(self):
        """
        Nạp model ngôn ngữ cho generation (Tối ưu cho model ~3B trên GPU).
        Model sẽ được tải ở chế độ bfloat16 để có hiệu năng tốt nhất.
        """
        if self.device != "cuda":
            logger.warning(f"Đang chạy trên {self.device}. Hiệu năng LLM sẽ rất chậm. GPU được khuyến nghị.")
            # Cho phép chạy trên CPU để test, nhưng cảnh báo người dùng.
        
        # Đọc token Hugging Face từ biến môi trường
        hf_token = os.getenv("HUGGING_FACE_TOKEN")
        if not hf_token:
            logger.error(f"[{self.school}] Lỗi tải LLM: Không tìm thấy biến môi trường HUGGING_FACE_TOKEN.")
            # Gán các thành phần là None để tránh lỗi sau này
            self.model = self.tokenizer = self.generator = None
            return

        try:
            logger.info(f"[{self.school}] Đang tải LLM model: {LLM_MODEL} ở chế độ bfloat16")
            
            self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL, token=hf_token)
            if self.tokenizer.pad_token is None:
                # Gán pad_token để tránh warning khi batching
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL,
                torch_dtype=torch.bfloat16,  # Tải trực tiếp ở định dạng bfloat16
                device_map="auto",           # Tự động map model lên GPU
                token=hf_token
            )

            # Pipeline vẫn giữ nguyên cấu trúc
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=MAX_LENGTH,
                temperature=TEMPERATURE,
                do_sample=True,
                top_p=0.9
            )

            logger.info(f"[{self.school}] ✓ Đã tải LLM model thành công ở chế độ bfloat16")

        except Exception as e:
            logger.error(f"[{self.school}] Lỗi tải LLM: {e}")
            self.model = None
            self.tokenizer = None
            self.generator = None

    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Tìm kiếm tài liệu liên quan từ vector database
        """
        if top_k is None:
            top_k = TOP_K_RETRIEVAL
        results = self.retriever.search(query, top_k=top_k)
        logger.info(f"[{self.school}] Tìm thấy {len(results)} đoạn văn liên quan")
        return results

    def generate_response(
        self,
        query: str,
        context: List[str],
        use_socratic: bool = False
    ) -> str:
        """
        Sinh câu trả lời dựa trên context và query
        """
        if self.generator is None or self.tokenizer is None:
            logger.warning(f"[{self.school}] Generator không khả dụng. Sử dụng fallback response.")
            return self._create_fallback_response(query, context, use_socratic)

        prompt = self._create_llama3_prompt(query, context, use_socratic)

        try:
            outputs = self.generator(prompt, return_full_text=False)
            response = outputs[0]['generated_text'] if outputs else ""
            response = self._clean_response(response)
        except Exception as e:
            logger.error(f"[{self.school}] Lỗi generation: {e}")
            response = self._create_fallback_response(query, context, use_socratic)
        return response

    def _create_llama3_prompt(
        self,
        query: str,
        context: List[str],
        use_socratic: bool = False
    ) -> str:
        """
        Tạo prompt theo định dạng chat của Llama 3
        """
        context_text = "\n\n".join(context[:3])

        system_message_content = (
            f"Bạn là một triết gia uyên bác chuyên về trường phái {self.school_info['name']}. "
            "Nhiệm vụ của bạn là trả lời câu hỏi của người dùng một cách ngắn gọn và súc tích, "
            "CHỈ DỰA VÀO 'Tài liệu tham khảo' được cung cấp. Không được sử dụng kiến thức bên ngoài. "
            "Luôn trả lời bằng tiếng Việt có đầy đủ dấu."
        )

        user_message_content = f"""
Tài liệu tham khảo:
---
{context_text}
---

Câu hỏi của người dùng: {query}
"""
        messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": user_message_content},
        ]
        
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt

    def _clean_response(self, response: str) -> str:
        """
        Làm sạch response từ model
        """
        return response.strip()

    def _create_fallback_response(
        self,
        query: str,
        context: List[str],
        use_socratic: bool = False
    ) -> str:
        """
        Tạo response đơn giản khi không có LLM
        """
        if not context:
            return f"Xin lỗi, tôi không tìm thấy thông tin về '{query}' trong tài liệu về {self.school_info['name']}."
        
        main_context = context[0] if context else ""
        
        if use_socratic:
            response = f"""Theo tài liệu về {self.school_info['name']}, {main_context[:200]}...

Để hiểu sâu hơn, bạn có thể suy ngẫm:
- Điều này có ý nghĩa gì với cuộc sống của bạn?
- Bạn có thể áp dụng nguyên lý này như thế nào?"""
        else:
            response = f"Dựa trên tài liệu về {self.school_info['name']}: {main_context[:300]}..."
        return response

    def answer(
        self,
        query: str,
        use_socratic: bool = True,
        return_sources: bool = True
    ) -> Dict:
        """
        Pipeline hoàn chỉnh: retrieve + generate
        """
        retrieved_docs = self.retrieve_context(query)

        if not retrieved_docs:
            return {
                "answer": f"Xin lỗi, tôi không tìm thấy thông tin về '{query}' trong tài liệu về {self.school_info['name']}. Câu hỏi này có thể nằm ngoài phạm vi kiến thức của tôi.",
                "sources": [],
                "confidence": 0.0
            }

        context_texts = [doc['text'] for doc in retrieved_docs]
        response = self.generate_response(query, context_texts, use_socratic=False)
        confidence = sum(doc['score'] for doc in retrieved_docs[:3]) / 3 if retrieved_docs else 0
        
        result = {"answer": response, "confidence": confidence}

        if return_sources:
            result["sources"] = [
                {
                    "text": doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
                    "score": doc['score'],
                    "chunk_id": doc['chunk_id']
                }
                for doc in retrieved_docs[:3]
            ]

        self.conversation_history.append({
            "query": query, "response": response, "timestamp": self._get_timestamp()
        })
        return result

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def reset_conversation(self):
        self.conversation_history = []
        logger.info(f"[{self.school}] Đã reset conversation history")


def test_rag_pipeline():
    """
    Test RAG pipeline với các trường phái khác nhau
    """
    test_cases = [
        ("stoicism", "Làm thế nào để kiểm soát cảm xúc?"),
        ("nihilism", "Cuộc sống có ý nghĩa không?"),
    ]

    for school, query in test_cases:
        print("\n" + "=" * 60)
        print(f"TRƯỜNG PHÁI: {PHILOSOPHY_SCHOOLS[school]['name']}")
        print(f"CÂU HỎI: {query}")
        print("-" * 60)
        rag = RAGPipeline(school, use_gpu=True)
        result = rag.answer(query, use_socratic=True, return_sources=True)
        print(f"\nTRẢ LỜI:")
        print(result['answer'])
        print(f"\nĐỘ TIN CẬY: {result['confidence']:.2%}")

        if 'sources' in result and result['sources']:
            print(f"\nNGUỒN THAM KHẢO:")
            for i, source in enumerate(result['sources'], 1):
                print(f"{i}. [Score: {source['score']:.3f}] {source['text']}")


if __name__ == "__main__":
    test_rag_pipeline()