import { Message, Philosopher } from "../types";

const API_BASE_URL = 'http://localhost:3001'; // URL của server backend

/**
 * Hàm này giờ đây chỉ gọi đến API backend của chúng ta.
 * Toàn bộ logic RAG đã được chuyển sang server.
 */
export const getRagResponse = async (
  query: string,
  philosopher: Philosopher,
  chatHistory: Message[]
): Promise<string> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        philosopher,
        chatHistory,
      }),
    });

    if (!response.ok) {
      throw new Error(`API call failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.reply;

  } catch (error) {
    console.error("Error calling backend API:", error);
    return "Xin lỗi, đã có lỗi kết nối đến máy chủ xử lý. Vui lòng thử lại sau.";
  }
};