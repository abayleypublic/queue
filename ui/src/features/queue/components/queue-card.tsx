interface QueueCardProps {
    position: number
    title: string;
    description: string;
}

const QueueCard = ({ position, title, description }: QueueCardProps) => (
    <div className="flex items-center gap-2">
        <div className="font-bold">{position}.</div>
        <div className="flex-1">
            <div className="font-bold">{title}</div>
            <div className="font-light">{description}</div>
        </div>
    </div>
);

export default QueueCard;