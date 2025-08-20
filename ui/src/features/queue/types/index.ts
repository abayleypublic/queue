export interface Entity {
    id: string
    name: string
}

export interface Queue {
    id: string
    entities: Array<Entity>
}