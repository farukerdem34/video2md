import { Plugin, Skill, Command } from "@opencode/plugin"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const ROOT = path.dirname(fileURLToPath(import.meta.url))

function parseFrontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  if (!m) return { meta: {}, body: text }
  const meta = {}
  for (const line of m[1].split(/\r?\n/)) {
    const idx = line.indexOf(":")
    if (idx > 0) {
      const k = line.slice(0, idx).trim()
      const v = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "")
      if (k) meta[k] = v
    }
  }
  return { meta, body: m[2].trim() }
}

function readDirSafe(dir) {
  try { return fs.readdirSync(dir, { withFileTypes: true }) } catch { return [] }
}

export default Plugin.define({
  id: "video2md",
  async setup(ctx) {
    // MCP server
    try {
      await ctx.mcp.transform((editor) => {
        editor.set("video2md", { type: "local", command: ["uvx", "--from", "git+https://github.com/farukerdem34/video2md", "video2md"], protocol: "legacy" })
      })
    } catch (e) { console.error("video2md mcp register failed", e) }

    // Skills from skills/*/SKILL.md
    try {
      await ctx.skill.transform((editor) => {
        const skillsDir = path.join(ROOT, "skills")
        for (const entry of readDirSafe(skillsDir)) {
          if (!entry.isDirectory()) continue
          const skillPath = path.join(skillsDir, entry.name, "SKILL.md")
          if (!fs.existsSync(skillPath)) continue
          const { meta, body } = parseFrontmatter(fs.readFileSync(skillPath, "utf8"))
          editor.add({
            id: Skill.ID.make(entry.name),
            name: Skill.Name.make(meta.name || entry.name),
            description: meta.description || (body.split("\n").find(Boolean) || entry.name),
            path: Skill.Info.fields.path.make(skillPath),
            content: body,
          })
        }
      })
    } catch (e) { console.error("video2md skills register failed", e) }

    // Commands from commands/*.md
    try {
      await ctx.command.transform((editor) => {
        const commandsDir = path.join(ROOT, "commands")
        for (const entry of readDirSafe(commandsDir)) {
          if (!entry.isFile() || !entry.name.endsWith(".md")) continue
          const filePath = path.join(commandsDir, entry.name)
          const { meta, body } = parseFrontmatter(fs.readFileSync(filePath, "utf8"))
          const name = entry.name.replace(/\.md$/, "")
          editor.add({
            name,
            description: meta.description,
            execute: async ({ sessionID, prompt, delivery }) => {
              const text = body.replace(/\$ARGUMENTS/g, prompt.text || "")
              await ctx.session.prompt({ ...prompt, sessionID, text, delivery })
            },
          })
        }
      })
    } catch (e) { console.error("video2md commands register failed", e) }
  },
})