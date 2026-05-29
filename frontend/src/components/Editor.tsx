// Tiptap 富文本编辑器（深色工具面板内）。
// tiptap-markdown 把内容序列化为 Markdown 喂后端 body_md（见复盘 D-03）。
// 支持 seed：外部"载入示例"时把内容灌进编辑器。

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Markdown } from "tiptap-markdown";
import { useEffect, type ReactNode } from "react";
import { Bold, Italic, Heading2, List, ListOrdered, Quote } from "lucide-react";

interface EditorProps {
  onMarkdownChange: (markdown: string) => void;
  // 外部注入内容：nonce 变化时把 markdown 灌入编辑器（用于"载入示例"）
  seed?: { markdown: string; nonce: number };
}

export default function Editor({ onMarkdownChange, seed }: EditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Markdown,
      Placeholder.configure({
        placeholder: "在这里粘贴或撰写原始内容，支持标题、列表、引用 …",
      }),
    ],
    content: "",
    onUpdate: ({ editor }) => {
      onMarkdownChange(editor.storage.markdown.getMarkdown());
    },
  });

  // seed.nonce 变化时灌入示例内容
  useEffect(() => {
    if (editor && seed && seed.nonce > 0) {
      editor.commands.setContent(seed.markdown);
      onMarkdownChange(editor.storage.markdown.getMarkdown());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed?.nonce, editor]);

  if (!editor) {
    return null;
  }

  return (
    <div className="flex h-full flex-col rounded-md border border-ink-700 bg-ink-850">
      <Toolbar editor={editor} />
      <div className="flex-1 overflow-y-auto px-5 py-4 text-[15px]">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

function Toolbar({ editor }: { editor: ReturnType<typeof useEditor> }) {
  if (!editor) {
    return null;
  }
  const base = "rounded p-1.5 text-paper-dim hover:bg-ink-800 hover:text-paper transition-colors";
  const active = "bg-ink-700 text-paper";
  return (
    <div className="flex flex-wrap items-center gap-0.5 border-b border-ink-700 px-2 py-1.5">
      <Btn cls={`${base} ${editor.isActive("bold") ? active : ""}`} on={() => editor.chain().focus().toggleBold().run()} label="加粗">
        <Bold size={15} />
      </Btn>
      <Btn cls={`${base} ${editor.isActive("italic") ? active : ""}`} on={() => editor.chain().focus().toggleItalic().run()} label="斜体">
        <Italic size={15} />
      </Btn>
      <Btn cls={`${base} ${editor.isActive("heading", { level: 2 }) ? active : ""}`} on={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} label="小标题">
        <Heading2 size={15} />
      </Btn>
      <Btn cls={`${base} ${editor.isActive("bulletList") ? active : ""}`} on={() => editor.chain().focus().toggleBulletList().run()} label="无序列表">
        <List size={15} />
      </Btn>
      <Btn cls={`${base} ${editor.isActive("orderedList") ? active : ""}`} on={() => editor.chain().focus().toggleOrderedList().run()} label="有序列表">
        <ListOrdered size={15} />
      </Btn>
      <Btn cls={`${base} ${editor.isActive("blockquote") ? active : ""}`} on={() => editor.chain().focus().toggleBlockquote().run()} label="引用">
        <Quote size={15} />
      </Btn>
    </div>
  );
}

function Btn({ children, cls, on, label }: { children: ReactNode; cls: string; on: () => void; label: string }) {
  return (
    <button type="button" className={cls} onClick={on} title={label} aria-label={label}>
      {children}
    </button>
  );
}
