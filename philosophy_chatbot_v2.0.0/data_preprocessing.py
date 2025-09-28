"""
Module xử lý dữ liệu và tạo vector database cho các trường phái triết học
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm

from config import (
    RAW_DATA_DIR, VECTOR_DB_DIR, PHILOSOPHY_SCHOOLS,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
)
from utils import (
    load_data_from_directory, clean_text,
    split_into_chunks, create_sample_data
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhilosophyDataProcessor:
    """
    Lớp xử lý dữ liệu triết học và tạo vector database
    """

    def __init__(self, school: str):
        """
        Khởi tạo processor cho một trường phái triết học
        
        Args:
            school: Tên trường phái (vd: 'stoicism', 'nihilism',...)
        """
        self.school = school
        self.school_info = PHILOSOPHY_SCHOOLS.get(school, {})
        self.data_dir = RAW_DATA_DIR / school
        self.vector_db_path = VECTOR_DB_DIR / f"{school}.faiss"
        self.metadata_path = VECTOR_DB_DIR / f"{school}_metadata.json"

        # Khởi tạo embedding model
        logger.info(f"Đang tải embedding model: {EMBEDDING_MODEL}")
        # SỬA LỖI: Chuyển embedding model sang CPU để tiết kiệm VRAM cho LLM
        self.encoder = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

        # Khởi tạo vector database
        self.index = None
        self.chunks = []
        self.metadata = []

    def process_data(self) -> bool:
        """
        Xử lý toàn bộ pipeline: đọc dữ liệu, tách chunks, tạo embeddings, lưu database
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Bước 1: Đọc dữ liệu từ thư mục
            logger.info(f"[{self.school}] Bước 1: Đọc dữ liệu từ {self.data_dir}")
            raw_text = load_data_from_directory(str(self.data_dir))

            if not raw_text:
                logger.warning(f"[{self.school}] Không tìm thấy dữ liệu!")
                return False

            # Bước 2: Làm sạch văn bản
            logger.info(f"[{self.school}] Bước 2: Làm sạch văn bản")
            clean_data = clean_text(raw_text)

            # Bước 3: Tách thành chunks
            logger.info(f"[{self.school}] Bước 3: Tách văn bản thành chunks")
            self.chunks = split_into_chunks(
                clean_data,
                chunk_size=CHUNK_SIZE,
                overlap=CHUNK_OVERLAP
            )
            logger.info(f"[{self.school}] Đã tạo {len(self.chunks)} chunks")

            # Bước 4: Tạo embeddings
            logger.info(f"[{self.school}] Bước 4: Tạo embeddings cho chunks")
            embeddings = self._create_embeddings()

            # Bước 5: Tạo FAISS index
            logger.info(f"[{self.school}] Bước 5: Tạo FAISS index")
            self._create_faiss_index(embeddings)

            # Bước 6: Lưu database và metadata
            logger.info(f"[{self.school}] Bước 6: Lưu vector database")
            self._save_database()

            logger.info(f"[{self.school}] ✓ Hoàn tất xử lý dữ liệu!")
            return True

        except Exception as e:
            logger.error(f"[{self.school}] Lỗi xử lý dữ liệu: {e}")
            return False

    def _create_embeddings(self) -> np.ndarray:
        """
        Tạo embeddings cho tất cả chunks
        
        Returns:
            Mảng numpy chứa embeddings
        """
        embeddings = []

        # Tạo embeddings theo batch để tối ưu
        batch_size = 32
        for i in tqdm(range(0, len(self.chunks), batch_size),
                      desc=f"Tạo embeddings cho {self.school}"):
            batch = self.chunks[i:i+batch_size]
            batch_embeddings = self.encoder.encode(
                batch,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            embeddings.extend(batch_embeddings)

        return np.array(embeddings).astype('float32')

    def _create_faiss_index(self, embeddings: np.ndarray):
        """
        Tạo FAISS index từ embeddings
        
        Args:
            embeddings: Mảng embeddings
        """
        # Lấy dimension của embeddings
        dim = embeddings.shape[1]

        # Tạo FAISS index với cosine similarity
        # Chuẩn hóa embeddings để dùng Inner Product ~ Cosine Similarity
        faiss.normalize_L2(embeddings)

        # Sử dụng IndexFlatIP cho Inner Product (tương đương Cosine sau khi chuẩn hóa)
        self.index = faiss.IndexFlatIP(dim)

        # Thêm vectors vào index
        self.index.add(embeddings)

        # Tạo metadata cho mỗi chunk
        self.metadata = [
            {
                "chunk_id": i,
                "text": chunk,
                "school": self.school,
                "length": len(chunk.split())
            }
            for i, chunk in enumerate(self.chunks)
        ]

    def _save_database(self):
        """
        Lưu FAISS index và metadata
        """
        # Lưu FAISS index
        faiss.write_index(self.index, str(self.vector_db_path))
        logger.info(f"Đã lưu FAISS index: {self.vector_db_path}")

        # Lưu metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu metadata: {self.metadata_path}")

    def load_database(self) -> bool:
        """
        Nạp lại database đã lưu
        
        Returns:
            True nếu thành công
        """
        try:
            # Nạp FAISS index
            self.index = faiss.read_index(str(self.vector_db_path))

            # Nạp metadata
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

            # Khôi phục chunks từ metadata
            self.chunks = [m['text'] for m in self.metadata]

            logger.info(f"[{self.school}] Đã nạp database với {len(self.chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"[{self.school}] Lỗi nạp database: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Tìm kiếm các chunks liên quan đến câu hỏi
        
        Args:
            query: Câu hỏi của người dùng
            top_k: Số lượng kết quả trả về
            
        Returns:
            Danh sách các chunks liên quan kèm metadata
        """
        if self.index is None:
            logger.error(f"[{self.school}] Database chưa được khởi tạo!")
            return []

        # Tạo embedding cho query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        faiss.normalize_L2(query_embedding)

        # Tìm kiếm trong FAISS
        distances, indices = self.index.search(query_embedding, top_k)

        # Tạo kết quả với metadata
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:  # FAISS trả về -1 nếu không tìm thấy
                result = {
                    "rank": i + 1,
                    "chunk_id": int(idx),
                    "text": self.chunks[idx],
                    "score": float(dist),
                    "metadata": self.metadata[idx]
                }
                results.append(result)

        return results


def process_all_schools():
    """
    Xử lý dữ liệu cho tất cả các trường phái triết học
    """
    logger.info("=" * 50)
    logger.info("BẮT ĐẦU XỬ LÝ DỮ LIỆU CHO TẤT CẢ TRƯỜNG PHÁI")
    logger.info("=" * 50)

    # Tạo dữ liệu mẫu nếu chưa có
    if not any((RAW_DATA_DIR / school).exists() for school in PHILOSOPHY_SCHOOLS):
        logger.info("Không tìm thấy dữ liệu, đang tạo dữ liệu mẫu...")
        create_sample_data()

    # Xử lý từng trường phái
    results = {}
    for school in PHILOSOPHY_SCHOOLS:
        logger.info(f"\n--- Xử lý trường phái: {PHILOSOPHY_SCHOOLS[school]['name']} ---")
        processor = PhilosophyDataProcessor(school)
        success = processor.process_data()
        results[school] = success

    # Báo cáo kết quả
    logger.info("\n" + "=" * 50)
    logger.info("KẾT QUẢ XỬ LÝ:")
    for school, success in results.items():
        status = "✓ Thành công" if success else "✗ Thất bại"
        logger.info(f"  {PHILOSOPHY_SCHOOLS[school]['name']}: {status}")
    logger.info("=" * 50)


def test_search(school: str = "stoicism", query: str = "Làm thế nào để kiểm soát cảm xúc?"):
    """
    Test chức năng tìm kiếm
    
    Args:
        school: Trường phái triết học
        query: Câu hỏi test
    """
    logger.info(f"\n--- TEST TÌM KIẾM ---")
    logger.info(f"Trường phái: {PHILOSOPHY_SCHOOLS[school]['name']}")
    logger.info(f"Câu hỏi: {query}")

    processor = PhilosophyDataProcessor(school)

    # Nạp database
    if processor.load_database():
        # Tìm kiếm
        results = processor.search(query, top_k=3)

        logger.info(f"\nTìm thấy {len(results)} kết quả:")
        for result in results:
            logger.info(f"\n[Rank {result['rank']}] Score: {result['score']:.4f}")
            logger.info(f"Chunk ID: {result['chunk_id']}")
            logger.info(f"Text: {result['text'][:200]}...")
    else:
        logger.error("Không thể nạp database!")


if __name__ == "__main__":
    # Xử lý dữ liệu cho tất cả trường phái
    process_all_schools()

    # Test tìm kiếm
    print("\n")
    test_search("stoicism", "Làm thế nào để kiểm soát cảm xúc?")
    test_search("nihilism", "Ý nghĩa của cuộc sống là gì?")