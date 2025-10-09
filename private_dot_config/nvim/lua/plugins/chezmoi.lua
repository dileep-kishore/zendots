return {
  {
    'xvzc/chezmoi.nvim',
    dependencies = { 'nvim-lua/plenary.nvim' },
    config = function()
    require("chezmoi").setup {
      -- your configurations
      vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
      pattern = { os.getenv("HOME") .. "/zendots/*" },
      callback = function(ev)
          local bufnr = ev.buf
          local edit_watch = function()
              require("chezmoi.commands.__edit").watch(bufnr)
          end
          vim.schedule(edit_watch)
      end,
})
    }
    end
  },
}
