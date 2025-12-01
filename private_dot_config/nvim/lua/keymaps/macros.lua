-- Macro functions for Neovim
local M = {}

-- Split sentences in paragraph to separate lines
-- Finds sentences ending with . ! or ? and moves them to new lines
M.split_sentences = function()
  -- Save cursor position
  local cursor_pos = vim.api.nvim_win_get_cursor(0)

  -- Get the current paragraph boundaries
  vim.cmd('normal! {')
  local start_line = vim.api.nvim_win_get_cursor(0)[1]
  vim.cmd('normal! }')
  local end_line = vim.api.nvim_win_get_cursor(0)[1]

  -- Adjust end_line if we're at the end of the file
  local total_lines = vim.api.nvim_buf_line_count(0)
  if end_line > total_lines then
    end_line = total_lines
  end

  -- If paragraph is only one line or empty, just return
  if start_line >= end_line then
    vim.api.nvim_win_set_cursor(0, cursor_pos)
    return
  end

  -- Perform substitution on the paragraph range
  -- Pattern matches: . ! or ? followed by one or more spaces, but not at line end
  -- Replace with the punctuation followed by a newline
  vim.cmd(string.format('%d,%ds/\\([.!?]\\)\\s\\+\\([A-Z]\\)/\\1\\r\\2/ge', start_line, end_line))

  -- Optional: restore cursor to approximate position
  -- (line number might have changed due to splits)
  pcall(vim.api.nvim_win_set_cursor, 0, cursor_pos)
end

return M
