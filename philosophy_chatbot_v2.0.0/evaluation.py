"""
Module đánh giá chất lượng hệ thống chatbot triết học
"""

import logging
import json
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
from pathlib import Path
import time

from config import PHILOSOPHY_SCHOOLS, EVALUATION_QUESTIONS, LOG_DIR
from socratic_wrapper import SocraticChatbot

# Cấu hình logging cho evaluation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChatbotEvaluator:
    """
    Lớp đánh giá chất lượng chatbot triết học
    """
    
    def __init__(self):
        """
        Khởi tạo evaluator
        """
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def evaluate_single_chatbot(
        self, 
        school: str,
        test_questions: List[str] = None,
        use_socratic: bool = True
    ) -> Dict:
        """
        Đánh giá một chatbot của trường phái
        
        Args:
            school: Tên trường phái
            test_questions: Danh sách câu hỏi test
            use_socratic: Sử dụng phương pháp Socrates
            
        Returns:
            Dictionary chứa kết quả đánh giá
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Đánh giá chatbot: {PHILOSOPHY_SCHOOLS[school]['name']}")
        logger.info(f"{'='*60}")
        
        # Khởi tạo chatbot
        try:
            chatbot = SocraticChatbot(school, use_gpu=True)
        except Exception as e:
            logger.error(f"Không thể khởi tạo chatbot {school}: {e}")
            return {
                "school": school,
                "status": "failed",
                "error": str(e)
            }
        
        # Lấy câu hỏi test
        if test_questions is None:
            test_questions = EVALUATION_QUESTIONS.get(school, [])
        
        # Thêm câu hỏi ngoài phạm vi
        out_of_scope_questions = [
            "Làm sao để lập trình Python?",
            "Công thức hóa học của nước là gì?",
            "Ai là tổng thống Mỹ hiện tại?"
        ]
        
        # Kết quả đánh giá
        evaluation_results = {
            "school": school,
            "school_name": PHILOSOPHY_SCHOOLS[school]["name"],
            "total_questions": len(test_questions) + len(out_of_scope_questions),
            "in_scope_questions": len(test_questions),
            "out_of_scope_questions": len(out_of_scope_questions),
            "responses": [],
            "metrics": {}
        }
        
        # Test với câu hỏi trong phạm vi
        logger.info("\n--- Test câu hỏi trong phạm vi ---")
        in_scope_results = []
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\nCâu hỏi {i}: {question}")
            
            start_time = time.time()
            result = chatbot.chat(question, use_socratic=use_socratic)
            response_time = time.time() - start_time
            
            # Đánh giá response
            has_sources = len(result.get("sources", [])) > 0
            is_socratic = result.get("type") == "socratic"
            confidence = result.get("confidence", 0.0)
            
            logger.info(f"Loại response: {result['type']}")
            logger.info(f"Độ tin cậy: {confidence:.2%}")
            logger.info(f"Có nguồn: {has_sources}")
            logger.info(f"Thời gian: {response_time:.2f}s")
            
            in_scope_results.append({
                "question": question,
                "response": result["response"][:200] + "...",
                "type": result["type"],
                "has_sources": has_sources,
                "confidence": confidence,
                "response_time": response_time,
                "is_correct": result["type"] != "rejection"
            })
        
        # Test với câu hỏi ngoài phạm vi
        logger.info("\n--- Test câu hỏi ngoài phạm vi ---")
        out_scope_results = []
        
        for i, question in enumerate(out_of_scope_questions, 1):
            logger.info(f"\nCâu hỏi ngoài phạm vi {i}: {question}")
            
            start_time = time.time()
            result = chatbot.chat(question, use_socratic=use_socratic)
            response_time = time.time() - start_time
            
            # Kiểm tra có từ chối đúng không
            is_rejection = result.get("type") == "rejection"
            
            logger.info(f"Đã từ chối: {is_rejection}")
            logger.info(f"Thời gian: {response_time:.2f}s")
            
            out_scope_results.append({
                "question": question,
                "response": result["response"][:200] + "...",
                "type": result["type"],
                "is_correct_rejection": is_rejection,
                "response_time": response_time
            })
        
        # Tính metrics
        evaluation_results["responses"] = {
            "in_scope": in_scope_results,
            "out_of_scope": out_scope_results
        }
        
        # Metrics cho câu hỏi trong phạm vi
        correct_in_scope = sum(1 for r in in_scope_results if r["is_correct"])
        with_sources = sum(1 for r in in_scope_results if r["has_sources"])
        socratic_responses = sum(1 for r in in_scope_results if r["type"] == "socratic")
        avg_confidence = sum(r["confidence"] for r in in_scope_results) / max(1, len(in_scope_results))
        avg_response_time_in = sum(r["response_time"] for r in in_scope_results) / max(1, len(in_scope_results))
        
        # Metrics cho câu hỏi ngoài phạm vi
        correct_rejections = sum(1 for r in out_scope_results if r["is_correct_rejection"])
        avg_response_time_out = sum(r["response_time"] for r in out_scope_results) / max(1, len(out_scope_results))
        
        evaluation_results["metrics"] = {
            "accuracy_in_scope": correct_in_scope / max(1, len(in_scope_results)),
            "source_citation_rate": with_sources / max(1, len(in_scope_results)),
            "socratic_rate": socratic_responses / max(1, len(in_scope_results)),
            "avg_confidence": avg_confidence,
            "rejection_accuracy": correct_rejections / max(1, len(out_scope_results)),
            "avg_response_time_in_scope": avg_response_time_in,
            "avg_response_time_out_scope": avg_response_time_out,
            "overall_accuracy": (correct_in_scope + correct_rejections) / (len(in_scope_results) + len(out_scope_results))
        }
        
        # Log tổng kết
        logger.info(f"\n--- KẾT QUẢ ĐÁNH GIÁ {PHILOSOPHY_SCHOOLS[school]['name']} ---")
        logger.info(f"Độ chính xác trong phạm vi: {evaluation_results['metrics']['accuracy_in_scope']:.1%}")
        logger.info(f"Tỷ lệ trích dẫn nguồn: {evaluation_results['metrics']['source_citation_rate']:.1%}")
        logger.info(f"Tỷ lệ phản hồi Socrates: {evaluation_results['metrics']['socratic_rate']:.1%}")
        logger.info(f"Độ tin cậy trung bình: {evaluation_results['metrics']['avg_confidence']:.1%}")
        logger.info(f"Độ chính xác từ chối: {evaluation_results['metrics']['rejection_accuracy']:.1%}")
        logger.info(f"Thời gian phản hồi TB: {evaluation_results['metrics']['avg_response_time_in_scope']:.2f}s")
        logger.info(f"Độ chính xác tổng thể: {evaluation_results['metrics']['overall_accuracy']:.1%}")
        
        # Lấy thống kê từ chatbot
        chatbot_stats = chatbot.get_stats()
        evaluation_results["chatbot_stats"] = chatbot_stats
        
        return evaluation_results
    
    def evaluate_all_chatbots(self, use_socratic: bool = True) -> Dict:
        """
        Đánh giá tất cả các chatbot
        
        Args:
            use_socratic: Sử dụng phương pháp Socrates
            
        Returns:
            Dictionary chứa kết quả đánh giá tổng hợp
        """
        logger.info("\n" + "="*70)
        logger.info("BẮT ĐẦU ĐÁNH GIÁ TOÀN BỘ HỆ THỐNG CHATBOT TRIẾT HỌC")
        logger.info("="*70)
        
        all_results = {
            "timestamp": self.timestamp,
            "use_socratic": use_socratic,
            "schools": {},
            "summary": {}
        }
        
        # Đánh giá từng trường phái
        for school in PHILOSOPHY_SCHOOLS.keys():
            try:
                result = self.evaluate_single_chatbot(school, use_socratic=use_socratic)
                all_results["schools"][school] = result
                time.sleep(1)  # Tránh overload
            except Exception as e:
                logger.error(f"Lỗi đánh giá {school}: {e}")
                all_results["schools"][school] = {
                    "school": school,
                    "status": "error",
                    "error": str(e)
                }
        
        # Tính metrics tổng hợp
        successful_schools = [
            school_data for school_data in all_results["schools"].values()
            if "metrics" in school_data
        ]
        
        if successful_schools:
            all_results["summary"] = {
                "total_schools": len(PHILOSOPHY_SCHOOLS),
                "successful_evaluations": len(successful_schools),
                "avg_accuracy_in_scope": sum(s["metrics"]["accuracy_in_scope"] for s in successful_schools) / len(successful_schools),
                "avg_source_citation_rate": sum(s["metrics"]["source_citation_rate"] for s in successful_schools) / len(successful_schools),
                "avg_socratic_rate": sum(s["metrics"]["socratic_rate"] for s in successful_schools) / len(successful_schools),
                "avg_rejection_accuracy": sum(s["metrics"]["rejection_accuracy"] for s in successful_schools) / len(successful_schools),
                "avg_confidence": sum(s["metrics"]["avg_confidence"] for s in successful_schools) / len(successful_schools),
                "avg_response_time": sum(s["metrics"]["avg_response_time_in_scope"] for s in successful_schools) / len(successful_schools),
                "avg_overall_accuracy": sum(s["metrics"]["overall_accuracy"] for s in successful_schools) / len(successful_schools)
            }
        
        # Lưu kết quả
        self.save_results(all_results)
        
        # In báo cáo tổng kết
        self.print_summary_report(all_results)
        
        return all_results
    
    def save_results(self, results: Dict):
        """
        Lưu kết quả đánh giá
        
        Args:
            results: Kết quả đánh giá
        """
        # Lưu JSON
        json_path = LOG_DIR / f"evaluation_{self.timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"\nĐã lưu kết quả JSON: {json_path}")
        
        # Lưu CSV cho metrics
        if results.get("summary"):
            csv_data = []
            for school, data in results["schools"].items():
                if "metrics" in data:
                    row = {"school": PHILOSOPHY_SCHOOLS[school]["name"]}
                    row.update(data["metrics"])
                    csv_data.append(row)
            
            if csv_data:
                df = pd.DataFrame(csv_data)
                csv_path = LOG_DIR / f"evaluation_metrics_{self.timestamp}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"Đã lưu metrics CSV: {csv_path}")
    
    def print_summary_report(self, results: Dict):
        """
        In báo cáo tổng kết
        
        Args:
            results: Kết quả đánh giá
        """
        print("\n" + "="*70)
        print("BÁO CÁO TỔNG KẾT ĐÁNH GIÁ HỆ THỐNG")
        print("="*70)
        
        if results.get("summary"):
            summary = results["summary"]
            print(f"\n📊 THỐNG KÊ TỔNG HỢP:")
            print(f"  • Số trường phái đánh giá: {summary['successful_evaluations']}/{summary['total_schools']}")
            print(f"  • Độ chính xác tổng thể: {summary['avg_overall_accuracy']:.1%}")
            print(f"  • Độ chính xác trong phạm vi: {summary['avg_accuracy_in_scope']:.1%}")
            print(f"  • Độ chính xác từ chối: {summary['avg_rejection_accuracy']:.1%}")
            print(f"  • Tỷ lệ trích dẫn nguồn: {summary['avg_source_citation_rate']:.1%}")
            print(f"  • Tỷ lệ sử dụng Socrates: {summary['avg_socratic_rate']:.1%}")
            print(f"  • Độ tin cậy trung bình: {summary['avg_confidence']:.1%}")
            print(f"  • Thời gian phản hồi TB: {summary['avg_response_time']:.2f}s")
        
        print("\n📋 CHI TIẾT TỪNG TRƯỜNG PHÁI:")
        for school, data in results["schools"].items():
            print(f"\n  {PHILOSOPHY_SCHOOLS[school]['name']}:")
            if "metrics" in data:
                print(f"    ✓ Độ chính xác: {data['metrics']['overall_accuracy']:.1%}")
                print(f"    ✓ Tỷ lệ từ chối đúng: {data['metrics']['rejection_accuracy']:.1%}")
                print(f"    ✓ Thời gian TB: {data['metrics']['avg_response_time_in_scope']:.2f}s")
            else:
                print(f"    ✗ Lỗi: {data.get('error', 'Unknown')}")
        
        print("\n" + "="*70)


def run_full_evaluation():
    """
    Chạy đánh giá đầy đủ cho toàn bộ hệ thống
    """
    evaluator = ChatbotEvaluator()
    
    # Đánh giá với phương pháp Socrates
    print("\n🔍 ĐÁNH GIÁ VỚI PHƯƠNG PHÁP SOCRATES")
    results_socratic = evaluator.evaluate_all_chatbots(use_socratic=True)
    
    # Đánh giá không dùng Socrates (để so sánh)
    evaluator.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("\n\n🔍 ĐÁNH GIÁ KHÔNG DÙNG SOCRATES (ĐỂ SO SÁNH)")
    results_direct = evaluator.evaluate_all_chatbots(use_socratic=False)
    
    # So sánh kết quả
    print("\n" + "="*70)
    print("SO SÁNH PHƯƠNG PHÁP SOCRATES VS TRỰC TIẾP")
    print("="*70)
    
    if results_socratic.get("summary") and results_direct.get("summary"):
        print("\n📊 Với Socrates:")
        print(f"  • Độ tin cậy TB: {results_socratic['summary']['avg_confidence']:.1%}")
        print(f"  • Tỷ lệ Socratic: {results_socratic['summary']['avg_socratic_rate']:.1%}")
        
        print("\n📊 Không Socrates:")
        print(f"  • Độ tin cậy TB: {results_direct['summary']['avg_confidence']:.1%}")
        print(f"  • Tỷ lệ Socratic: {results_direct['summary']['avg_socratic_rate']:.1%}")
    
    print("\n✅ Hoàn tất đánh giá hệ thống!")
    print(f"📁 Kết quả được lưu tại: {LOG_DIR}")


def run_single_school_test(school: str = "stoicism"):
    """
    Test đánh giá cho một trường phái cụ thể
    
    Args:
        school: Tên trường phái cần test
    """
    print(f"\n🧪 TEST ĐÁNH GIÁ CHO {PHILOSOPHY_SCHOOLS[school]['name'].upper()}")
    print("="*60)
    
    evaluator = ChatbotEvaluator()
    
    # Câu hỏi test tùy chỉnh
    custom_questions = [
        "Làm thế nào để sống tốt?",
        "Ý nghĩa của cuộc sống là gì?",
        "Con người có tự do không?"
    ]
    
    result = evaluator.evaluate_single_chatbot(
        school,
        test_questions=custom_questions,
        use_socratic=True
    )
    
    # In kết quả chi tiết
    if "metrics" in result:
        print("\n📈 KẾT QUẢ METRICS:")
        for metric, value in result["metrics"].items():
            if isinstance(value, float):
                if "time" in metric:
                    print(f"  • {metric}: {value:.2f}s")
                else:
                    print(f"  • {metric}: {value:.1%}")
    
    print("\n✅ Hoàn tất test!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "full":
            # Chạy đánh giá đầy đủ
            run_full_evaluation()
        elif sys.argv[1] in PHILOSOPHY_SCHOOLS:
            # Test một trường phái cụ thể
            run_single_school_test(sys.argv[1])
        else:
            print(f"Lệnh không hợp lệ: {sys.argv[1]}")
            print(f"Sử dụng: python evaluation.py [full|{' | '.join(PHILOSOPHY_SCHOOLS.keys())}]")
    else:
        # Mặc định chạy đánh giá đầy đủ
        run_full_evaluation()