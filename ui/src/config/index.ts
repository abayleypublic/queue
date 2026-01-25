interface APIConfig {
    api_url: string
    queue: string
    account_url: string
}

interface Config {
    apiURL: string
    queue: string
    accountURL: string
}

let config: Config = {
    apiURL: '',
    queue: '',
    accountURL: '',
}
try {
    const res = await fetch('/config.json')
    const json = await res.json() as APIConfig
    config = {
        apiURL: json.api_url,
        queue: json.queue,
        accountURL: json.account_url,
    }
} catch (error) {
    console.error('error loading config:', error)
}

export default config