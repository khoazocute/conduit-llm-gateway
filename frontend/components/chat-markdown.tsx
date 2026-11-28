import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Câu trả lời của mô hình là Markdown (chữ đậm, danh sách, khối code, bảng).
// An toàn: KHÔNG bật rehype-raw, nên HTML thô trong câu trả lời chỉ hiện như chữ, không chạy.
// react-markdown tự chặn link "javascript:". Ảnh bị tắt (chỉ giữ chữ) để câu trả lời
// không thể tự tải ảnh từ máy chủ lạ.
export function ChatMarkdown({ text }: { text: string }) {
  return (
    <div className="chat-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        disallowedElements={["img"]}
        unwrapDisallowed
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer nofollow">
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
