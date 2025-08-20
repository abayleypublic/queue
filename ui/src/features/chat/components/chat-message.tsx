interface ChatMessageProps {
    actor: string
    text: string
}

const ChatMessage = ({ actor, text }: ChatMessageProps) => (
    <>
        <div className="flex-shrink-0 ali">
            <span className="font-bold">{actor === "assistant" ? "🤖" : "🧍‍♂️"}</span>
        </div>
        <div className="flex-1">
            <p>{text}</p>
        </div>
    </>
)


export default ChatMessage