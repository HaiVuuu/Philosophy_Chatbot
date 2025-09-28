"""
Wrapper cho chatbot sử dụng phương pháp Socrates
Đặt câu hỏi phản tư thay vì chỉ trả lời trực tiếp
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime

from config import PHILOSOPHY_SCHOOLS, SOCRATIC_SYSTEM_PROMPT
from rag_pipeline import RAGPipeline

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocraticChatbot:
    """
    Chatbot triết học sử dụng phương pháp Socrates
    """
    
    # Mẫu câu hỏi Socrates cho từng trường phái
    SOCRATIC_QUESTIONS = {
        "stoicism": [
            "Điều gì trong tình huống này nằm trong tầm kiểm soát của bạn?",
            "Cảm xúc này đến từ đâu - từ sự kiện hay từ cách bạn nhìn nhận sự kiện?",
            "Làm sao để chấp nhận những gì không thể thay đổi?",
            "Đức hạnh nào bạn cần rèn luyện trong hoàn cảnh này?",
            "Nếu Marcus Aurelius ở trong tình huống của bạn, ông ấy sẽ suy nghĩ gì?"
        ],
        "nihilism": [
            "Nếu không có ý nghĩa vốn có, bạn có thể tự tạo ra ý nghĩa nào?",
            "Việc chấp nhận vô nghĩa giải phóng hay giam hãm bạn?",
            "Sau khi 'Thượng đế chết', điều gì thay thế các giá trị cũ?",
            "Bạn có đang trốn chạy khỏi tự do bằng cách tìm kiếm ý nghĩa tuyệt đối?",
            "Hư vô là điểm kết thúc hay điểm khởi đầu cho cuộc sống của bạn?"
        ],
        "phenomenology": [
            "Bạn đang trải nghiệm điều này như thế nào trong ý thức?",
            "Khi gạt bỏ mọi giả định, bản thân sự việc hiện ra với bạn ra sao?",
            "Thân thể bạn tham gia như thế nào vào trải nghiệm này?",
            "Ý thức của bạn đang hướng về đối tượng nào?",
            "Thời gian được trải nghiệm thế nào trong khoảnh khắc này?"
        ],
        "voluntarism": [
            "Ý chí của bạn thực sự tự do hay bị điều kiện hóa?",
            "Khao khát này xuất phát từ đâu - từ bản thân hay từ xã hội?",
            "Khi nào ý chí trở thành gông cùm thay vì sức mạnh?",
            "Bạn đang muốn điều gì đằng sau điều bạn nghĩ mình muốn?",
            "Làm sao để vượt qua ý chí mù quáng hướng tới ý chí sáng tạo?"
        ],
        "marxism": [
            "Vị trí giai cấp của bạn ảnh hưởng thế nào đến cách nhìn vấn đề?",
            "Ai được lợi từ cách tổ chức hiện tại của xã hội?",
            "Bạn có đang tái sản xuất hệ tư tưởng thống trị không?",
            "Lao động của bạn bị tha hóa như thế nào?",
            "Mâu thuẫn nào trong xã hội đang thúc đẩy sự thay đổi?"
        ],
        "existentialism": [
            "Bạn đang chọn hay đang để hoàn cảnh chọn cho bạn?",
            "Trách nhiệm nào đi kèm với tự do này?",
            "Bạn có đang sống chân thực hay đang tự lừa dối mình?",
            "Lo âu này nói gì về tự do và khả năng của bạn?",
            "Làm sao để sống ý nghĩa trong một thế giới phi lý?"
        ]
    }
    
    # Mẫu câu dẫn nhập cho phương pháp Socrates
    SOCRATIC_INTROS = [
        "Thật thú vị khi bạn hỏi về điều này. Hãy cùng khám phá sâu hơn:",
        "Câu hỏi của bạn mở ra nhiều góc nhìn. Trước tiên, hãy suy ngẫm:",
        "Để hiểu rõ hơn, chúng ta cần đặt câu hỏi:",
        "Tôi không có câu trả lời tuyệt đối, nhưng hãy cùng tìm hiểu:",
        "Trí tuệ bắt đầu từ việc đặt câu hỏi đúng:"
    ]
    
    def __init__(self, school: str, use_gpu: bool = False):
        """
        Khởi tạo Socratic Chatbot cho một trường phái
        
        Args:
            school: Tên trường phái triết học
            use_gpu: Sử dụng GPU nếu có
        """
        self.school = school
        self.school_info = PHILOSOPHY_SCHOOLS.get(school, {})
        
        # Khởi tạo RAG pipeline
        self.rag_pipeline = RAGPipeline(school, use_gpu)
        
        # Lịch sử hội thoại cho context
        self.conversation_history = []
        
        # Thống kê cho đánh giá
        self.stats = {
            "total_questions": 0,
            "answered_questions": 0,
            "rejected_questions": 0,
            "socratic_responses": 0
        }
        
        logger.info(f"[{school}] Đã khởi tạo Socratic Chatbot")
    
    def generate_socratic_questions(self, topic: str, context: str) -> List[str]:
        """
        Tạo câu hỏi Socrates phù hợp với chủ đề và context
        
        Args:
            topic: Chủ đề của câu hỏi
            context: Context từ retrieval
            
        Returns:
            Danh sách 1-2 câu hỏi Socrates
        """
        # Lấy câu hỏi mẫu cho trường phái
        questions_pool = self.SOCRATIC_QUESTIONS.get(self.school, [])
        
        # Chọn ngẫu nhiên 1-2 câu hỏi
        num_questions = random.randint(1, 2)
        selected_questions = random.sample(questions_pool, min(num_questions, len(questions_pool)))
        
        # Có thể customize câu hỏi dựa trên topic (nâng cao)
        # Ở đây ta dùng câu hỏi mẫu trực tiếp
        
        return selected_questions
    
    def create_socratic_response(
        self, 
        query: str, 
        answer: str,
        sources: List[Dict]
    ) -> str:
        """
        Tạo response theo phong cách Socrates
        
        Args:
            query: Câu hỏi gốc
            answer: Câu trả lời từ RAG
            sources: Nguồn tham khảo
            
        Returns:
            Response theo phương pháp Socrates
        """
        # Chọn câu dẫn nhập ngẫu nhiên
        intro = random.choice(self.SOCRATIC_INTROS)
        
        # Tóm tắt ngắn gọn từ answer (1-2 câu)
        # Ở đây ta cắt ngắn answer
        sentences = answer.split('.')
        brief_explanation = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else answer
        
        # Tạo câu hỏi Socrates
        context_text = sources[0]['text'] if sources else ""
        socratic_questions = self.generate_socratic_questions(query, context_text)
        
        # Ghép thành response hoàn chỉnh
        response_parts = [intro, brief_explanation, "\n\n💭 Hãy suy ngẫm thêm:"]
        
        for i, question in enumerate(socratic_questions, 1):
            response_parts.append(f"{i}. {question}")
        
        # Thêm lời khuyên khám phá
        response_parts.append(
            f"\n\n📚 Theo truyền thống {self.school_info['name']}, "
            f"việc tự tìm câu trả lời qua phản tư sẽ giúp bạn hiểu sâu hơn."
        )
        
        return "\n".join(response_parts)
    
    def is_out_of_scope(self, query: str, retrieved_docs: List[Dict]) -> bool:
        """
        Kiểm tra câu hỏi có nằm ngoài phạm vi không
        
        Args:
            query: Câu hỏi
            retrieved_docs: Tài liệu tìm được
            
        Returns:
            True nếu ngoài phạm vi
        """
        # Kiểm tra điểm số của tài liệu tìm được
        if not retrieved_docs:
            return True
        
        # Nếu điểm cao nhất < ngưỡng → ngoài phạm vi
        top_score = retrieved_docs[0]['score'] if retrieved_docs else 0
        threshold = 0.3  # Ngưỡng có thể điều chỉnh
        
        if top_score < threshold:
            return True
        
        # Kiểm tra keywords không liên quan
        irrelevant_keywords = [
            'khoa học máy tính', 'lập trình', 'công nghệ',
            'y học', 'vật lý', 'hóa học', 'toán học thuần túy'
        ]
        
        query_lower = query.lower()
        for keyword in irrelevant_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def create_rejection_response(self, query: str) -> str:
        """
        Tạo câu từ chối lịch sự khi câu hỏi ngoài phạm vi
        
        Args:
            query: Câu hỏi bị từ chối
            
        Returns:
            Câu từ chối lịch sự
        """
        rejections = [
            f"Xin lỗi, câu hỏi về '{query[:50]}...' nằm ngoài phạm vi kiến thức {self.school_info['name']} của tôi. "
            f"Tôi chỉ có thể thảo luận về các chủ đề liên quan đến {self.school_info['description']}.",
            
            f"Tôi hiểu bạn muốn biết về điều này, nhưng với tư cách là chatbot chuyên về {self.school_info['name']}, "
            f"tôi không có đủ thông tin để trả lời câu hỏi này một cách chính xác.",
            
            f"Câu hỏi thú vị! Tuy nhiên, nó vượt ra khỏi lĩnh vực {self.school_info['name']} mà tôi được đào tạo. "
            f"Bạn có câu hỏi nào về {self.school_info['description']} không?"
        ]
        
        return random.choice(rejections)
    
    def chat(
        self, 
        query: str,
        use_socratic: bool = True,
        return_sources: bool = True
    ) -> Dict:
        """
        Xử lý chat với người dùng
        
        Args:
            query: Câu hỏi từ người dùng
            use_socratic: Sử dụng phương pháp Socrates
            return_sources: Trả về nguồn tham khảo
            
        Returns:
            Dictionary chứa response và metadata
        """
        # Cập nhật thống kê
        self.stats["total_questions"] += 1
        
        # Gọi RAG pipeline để lấy câu trả lời cơ bản
        rag_result = self.rag_pipeline.answer(
            query, 
            use_socratic=False,  # Lấy raw answer trước
            return_sources=return_sources
        )
        
        # Kiểm tra nếu câu hỏi ngoài phạm vi
        retrieved_docs = self.rag_pipeline.retrieve_context(query)
        if self.is_out_of_scope(query, retrieved_docs):
            self.stats["rejected_questions"] += 1
            
            response = self.create_rejection_response(query)
            result = {
                "response": response,
                "type": "rejection",
                "sources": [],
                "confidence": 0.0
            }
        else:
            self.stats["answered_questions"] += 1
            
            # Tạo response theo phương pháp Socrates nếu cần
            if use_socratic:
                self.stats["socratic_responses"] += 1
                response = self.create_socratic_response(
                    query,
                    rag_result["answer"],
                    rag_result.get("sources", [])
                )
                response_type = "socratic"
            else:
                response = rag_result["answer"]
                response_type = "direct"
            
            result = {
                "response": response,
                "type": response_type,
                "sources": rag_result.get("sources", []),
                "confidence": rag_result.get("confidence", 0.0)
            }
        
        # Lưu vào lịch sử
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": result["response"],
            "type": result["type"]
        })
        
        # Giới hạn lịch sử (giữ 10 câu gần nhất)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return result
    
    def get_conversation_context(self) -> str:
        """
        Lấy context từ lịch sử hội thoại
        
        Returns:
            Context dạng text
        """
        if not self.conversation_history:
            return ""
        
        context_parts = []
        for conv in self.conversation_history[-3:]:  # 3 câu gần nhất
            context_parts.append(f"Người dùng: {conv['query']}")
            context_parts.append(f"Chatbot: {conv['response'][:200]}...")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """
        Lấy thống kê về chatbot
        
        Returns:
            Dictionary chứa các thống kê
        """
        stats = self.stats.copy()
        
        # Tính tỷ lệ
        if stats["total_questions"] > 0:
            stats["answer_rate"] = stats["answered_questions"] / stats["total_questions"]
            stats["rejection_rate"] = stats["rejected_questions"] / stats["total_questions"]
            stats["socratic_rate"] = stats["socratic_responses"] / max(1, stats["answered_questions"])
        else:
            stats["answer_rate"] = 0
            stats["rejection_rate"] = 0
            stats["socratic_rate"] = 0
        
        return stats
    
    def reset(self):
        """
        Reset chatbot về trạng thái ban đầu
        """
        self.conversation_history = []
        self.stats = {
            "total_questions": 0,
            "answered_questions": 0,
            "rejected_questions": 0,
            "socratic_responses": 0
        }
        self.rag_pipeline.reset_conversation()
        logger.info(f"[{self.school}] Đã reset Socratic Chatbot")


def test_socratic_chatbot():
    """
    Test Socratic Chatbot với các trường phái khác nhau
    """
    test_cases = [
        # Câu hỏi trong phạm vi
        ("stoicism", "Làm thế nào để kiểm soát cảm xúc khi gặp khó khăn?"),
        ("nihilism", "Nếu cuộc sống vô nghĩa thì tại sao phải sống?"),
        ("existentialism", "Tự do và trách nhiệm có mâu thuẫn không?"),
        
        # Câu hỏi ngoài phạm vi
        ("stoicism", "Làm sao để lập trình Python hiệu quả?"),
        ("marxism", "Công thức hóa học của nước là gì?"),
    ]
    
    for school, query in test_cases:
        print("\n" + "="*70)
        print(f"TRƯỜNG PHÁI: {PHILOSOPHY_SCHOOLS[school]['name']}")
        print(f"CÂU HỎI: {query}")
        print("-"*70)
        
        # Tạo chatbot
        chatbot = SocraticChatbot(school, use_gpu=True)
        
        # Chat với phương pháp Socrates
        result = chatbot.chat(query, use_socratic=True)
        
        print(f"\nLOẠI PHẢN HỒI: {result['type']}")
        print(f"\nPHẢN HỒI:")
        print(result['response'])
        
        if result['sources']:
            print(f"\nĐỘ TIN CẬY: {result['confidence']:.2%}")
            print(f"\nNGUỒN THAM KHẢO:")
            for i, source in enumerate(result['sources'][:2], 1):
                print(f"{i}. {source['text'][:100]}...")
        
        # In thống kê
        stats = chatbot.get_stats()
        print(f"\nTHỐNG KÊ:")
        print(f"- Tổng câu hỏi: {stats['total_questions']}")
        print(f"- Tỷ lệ trả lời: {stats['answer_rate']:.0%}")
        print(f"- Tỷ lệ từ chối: {stats['rejection_rate']:.0%}")


if __name__ == "__main__":
    test_socratic_chatbot()