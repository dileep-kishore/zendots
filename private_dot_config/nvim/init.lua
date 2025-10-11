-- bootstrap lazy.nvim, LazyVim and your plugins
require("options")
require("autocmds")
require("config.lazy")
require("keymaps")
require("ipynb")
vim.cmd.colorscheme("catppuccin")
