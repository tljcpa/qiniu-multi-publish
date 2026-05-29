// Tiptap 富文本编辑器组件。
// 通过 tiptap-markdown 把编辑内容序列化成 Markdown，正好喂后端 body_md（见复盘 D-03）。

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Markdown } from "tiptap-markdown";
import { useEffect, type ReactNode } from "react";
import {
  Bold,
  Italic,
  Heading2,
  List,
  ListOrdered,
  Quote,
} from "lucide-react";

interface EditorProps {
  // 内容变化时回调，向上抛出最新的 Markdown
  onMarkdownChange: (markdown: string) => void;
  initialMarkdown?: string;
}

export default function Editor({ onMarkdownChange, initialMarkdown }: EditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Markdown,
      Placeholder.configure({
        placeholder: "在这里粘贴或撰写你的原始内容，支持标题、列表、引用…",
      }),
    ],
    content: initialMarkdown ?? "",
    onUpdate: ({ editor }) => {
      // 取出 Markdown 抛给父组件
      const md = editor.storage.markdown.getMarkdown();
      onMarkdownChange(md);
    },
  });

  // 首次挂载时同步一次初始 Markdown
  useEffect(() => {
    if (editor && initialMarkdown) {
      onMarkdownChange(editor.storage.markdown.getMarkdown());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor]);

  if (!editor) {
    return null;
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
      <Toolbar editor={editor} />
      <div className="flex-1 overflow-y-auto px-5 py-4 text-[15px] text-gray-800">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

// 工具栏：常用富文本操作
function Toolbar({ editor }: { editor: ReturnType<typeof useEditor> }) {
  if (!editor) {
    return null;
  }
  const btn = "rounded-md p-2 text-gray-600 hover:bg-gray-100 transition-colors";
  const active = "bg-gray-200 text-gray-900";
  return (
    <div className="flex flex-wrap items-center gap-1 border-b border-gray-100 px-3 py-2">
      <ToolButton
        className={`${btn} ${editor.isActive("bold") ? active : ""}`}
        onClick={() => editor.chain().focus().toggleBold().run()}
        label="加粗"
      >
        <Bold size={16} />
      </ToolButton>
      <ToolButton
        className={`${btn} ${editor.isActive("italic") ? active : ""}`}
        onClick={() => editor.chain().focus().toggleItalic().run()}
        label="斜体"
      >
        <Italic size={16} />
      </ToolButton>
      <ToolButton
        className={`${btn} ${editor.isActive("heading", { level: 2 }) ? active : ""}`}
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        label="标题"
      >
        <Heading2 size={16} />
      </ToolButton>
      <ToolButton
        className={`${btn} ${editor.isActive("bulletList") ? active : ""}`}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        label="无序列表"
      >
        <List size={16} />
      </ToolButton>
      <ToolButton
        className={`${btn} ${editor.isActive("orderedList") ? active : ""}`}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        label="有序列表"
      >
        <ListOrdered size={16} />
      </ToolButton>
      <ToolButton
        className={`${btn} ${editor.isActive("blockquote") ? active : ""}`}
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        label="引用"
      >
        <Quote size={16} />
      </ToolButton>
    </div>
  );
}

function ToolButton({
  children,
  className,
  onClick,
  label,
}: {
  children: ReactNode;
  className: string;
  onClick: () => void;
  label: string;
}) {
  return (
    <button type="button" className={className} onClick={onClick} title={label} aria-label={label}>
      {children}
    </button>
  );
}
