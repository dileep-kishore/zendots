return {
  {
    "epwalsh/obsidian.nvim",
    event = "VeryLazy",
    ft = { "markdown" },
    config = function()
      require("obsidian").setup({
        disable_frontmatter = true,
        legacy_commands = false,
        workspaces = {
          {
            name = "LifeOS",
            path = "~/Documents/LifeOS",
          },
        },
        new_notes_location = "notes_subdir",
        notes_subdir = "00_Inbox",
        preferred_link_style = "wiki",
        note_id_func = function(title)
          return title
        end,
        daily_notes = {
          folder = "01_TimeFrames/011_Daily",
          date_format = "%Y-%m-%d",
          template = "_Templates/timeframes/DailyTemplate.md",
        },
        templates = {
          folder = "_Templates",
          date_format = "%Y-%m-%d",
          time_format = "%H:%M",
          substitutions = {},
        },
        completion = {
          min_chars = 2,
          nvim_cmp = false,
          blink = true,
        },
        picker = { name = "snacks.pick" },
        ui = { enable = false },
        attachments = {
          img_folder = "_Assets",
        },
      })
    end,
    keys = {
      { "<leader>nn", "<cmd>ObsidianNew<cr>", desc = "Obsidian new note" },
      { "<leader>nf", "<cmd>ObsidianQuickSwitch<cr>", desc = "Obsidian quick switch" },
      { "<leader>nd", "<cmd>ObsidianToday<cr>", desc = "Obsidian today" },
      { "<leader>nt", "<cmd>ObsidianTemplate<cr>", desc = "Obsidian template" },
      { "<leader>nk", "<cmd>ObsidianLink<cr>", mode = "v", desc = "Obsidian link" },
      { "<leader>nb", "<cmd>ObsidianBacklinks<cr>", desc = "Obsidian backlinks" },
      { "<leader>nl", "<cmd>ObsidianLinks<cr>", desc = "Obsidian links" },
      { "<leader>nr", "<cmd>ObsidianRename<cr>", desc = "Obsidian rename" },
      { "<leader>no", "<cmd>ObsidianTOC<cr>", desc = "Obsidian table of contents" },
    },
  },
}
