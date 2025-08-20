import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useTheme } from "@/features/theme/hooks/use-theme"

const ThemeToggle = () => {
    const { setTheme, theme } = useTheme()

    return <>
        <Switch
            id="theme"
            checked={theme === "dark"}
            onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
        />
        <Label htmlFor="theme" className="font-extralight">Dark Mode</Label>
    </>
}

export default ThemeToggle