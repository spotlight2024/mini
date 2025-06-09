# 推荐开发者高效终端与工具清单

非常推荐以下工具，能极大提升你的终端和开发效率：

---

## 1. 命令行效率工具

- **fzf**  
  模糊查找历史命令、文件、git 分支等，极大提升查找和补全效率。

- **thefuck**  
  自动纠正命令拼写错误，输错命令后输入 `fuck` 自动修正并执行。

  ```bash
  brew install thefuck
  echo 'eval $(thefuck --alias)' >> ~/.zshrc
  ```

- **bat**  
  彩色高亮的 cat，支持代码语法高亮和行号。

  ```bash
  brew install bat
  ```

- **lsd**  
  彩色美观的 ls，支持图标和更好的人类可读性。

  ```bash
  brew install lsd
  ```

- **htop**  
  交互式进程管理器，比 top 更直观。

  ```bash
  brew install htop
  ```

- **ripgrep (rg)**  
  超快的代码/文本搜索工具，比 grep/ag 更快更好用。

  ```bash
  brew install ripgrep
  ```

---

## 2. Git 相关

- **tig**  
  终端下的 git 可视化工具，查看提交历史、diff、分支非常方便。

  ```bash
  brew install tig
  ```

- **delta**  
  美化 git diff/patch 输出，彩色高亮，极易阅读。

  ```bash
  brew install git-delta
  ```

---

## 3. 终端美化与效率

- **powerlevel10k**  
  超强 zsh 主题，极致美观和信息量，支持图标、git 状态、右侧提示等。

  ```bash
  git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/.oh-my-zsh/custom/themes/powerlevel10k
  # 然后在 ~/.zshrc 设置 ZSH_THEME="powerlevel10k/powerlevel10k"
  ```

- **Nerd Font**  
  配合 powerlevel10k/lsd 显示图标，推荐 [MesloLGS NF](https://github.com/romkatv/powerlevel10k#manual-font-installation)。

---

## 4. Python/开发相关

- **pipx**  
  隔离安装和运行 Python 命令行工具。

  ```bash
  brew install pipx
  pipx ensurepath
  ```

- **httpie**  
  更现代、易用的 http 命令行客户端，替代 curl。

  ```bash
  brew install httpie
  ```

---

## 5. 其它推荐

- **z**  
  目录跳转神器，频繁访问的目录可直接 `z dirname` 跳转。

  ```bash
  brew install z
  ```

- **autojump**  
  另一个目录跳转工具。

  ```bash
  brew install autojump
  echo '[ -f /usr/local/etc/profile.d/autojump.sh ] && . /usr/local/etc/profile.d/autojump.sh' >> ~/.zshrc
  ```

---

## 总结

这些工具大多可通过 Homebrew 一键安装，极大提升你的开发效率和终端体验。
如需某个工具的详细配置或用法，随时问我！

**祝你开发愉快，效率飞升！** 