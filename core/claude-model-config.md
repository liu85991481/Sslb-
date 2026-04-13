# Claude Code 单独配置模型方法

## 需求场景
在同一台机器上，不同项目需要使用不同的 API 接口或模型。

## 成功方法

### 1. 创建配置文件
在项目目录下创建 `.claude` 文件夹，并在其中创建 `settings.local.json`：

```
项目目录/.claude/settings.local.json
```

### 2. 配置内容
```json
{
  "apiKey": "你的API密钥",
  "baseUrl": "API地址",
  "model": "模型名称",
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "你的API密钥",
    "ANTHROPIC_BASE_URL": "API地址",
    "ANTHROPIC_MODEL": "模型名称"
  }
}
```

### 3. 创建启动脚本
在项目目录下创建 `start.bat`：

```bat
@echo off
cd /d "%~dp0"
claude
```

### 4. 运行
双击 `start.bat` 即可在该目录下使用指定的模型。

## 优先级说明
- `settings.local.json` 会覆盖全局 `settings.json` 的配置
- 确保全局配置中的模型与你需要的不冲突

## 示例：本项目配置
- 目录：`D:\sslb\core\`
- API：`https://api.toskaxy.xyz`
- 模型：`gpt-5.4`
