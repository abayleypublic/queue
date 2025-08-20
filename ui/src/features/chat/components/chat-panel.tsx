import type { PropsWithChildren } from "react"
import { useEffect, useRef } from "react"

interface ChatPanelProps extends PropsWithChildren { }

const ChatPanel = ({ children }: ChatPanelProps) => {
    const panelRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const panel = panelRef.current;
        if (panel) {
            panel.scrollTop = panel.scrollHeight;
        }
    }, [children]);

    return (
        <div
            ref={panelRef}
            className="
                chat-panel 
                rounded-lg 
                shadow 
                backdrop-blur-md 
                max-h-64
                overflow-auto 
                bg-white 
                dark:bg-gray-900 
                py-4
                px-8
            "
        >
            {children}
        </div>
    );
}

export default ChatPanel