# Shared model choice for the coordinator and every subagent, so they don't
# silently drift onto the CLI's default model if a definition forgets to set
# its own `model` field.
MODEL = "claude-haiku-4-5"
