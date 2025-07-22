import * as fs from "fs/promises";

export class Logger {
  private logFile?: string;

  constructor(logFile?: string) {
    this.logFile = logFile;
  }

  private formatMessage(level: string, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] ${level.toUpperCase()}: ${message}`;
  }

  private async writeToFile(message: string): Promise<void> {
    if (this.logFile) {
      try {
        await fs.appendFile(this.logFile, message + "\n");
      } catch (error) {
        console.error("Failed to write to log file:", error);
      }
    }
  }

  async info(message: string): Promise<void> {
    const formatted = this.formatMessage("info", message);
    console.log(formatted);
    await this.writeToFile(formatted);
  }

  async warn(message: string): Promise<void> {
    const formatted = this.formatMessage("warn", message);
    console.warn(formatted);
    await this.writeToFile(formatted);
  }

  async error(message: string, error?: Error): Promise<void> {
    const errorDetails = error ? ` - ${error.message}` : "";
    const formatted = this.formatMessage("error", message + errorDetails);
    console.error(formatted);
    await this.writeToFile(formatted);

    if (error && error.stack) {
      await this.writeToFile(error.stack);
    }
  }

  async debug(message: string): Promise<void> {
    const formatted = this.formatMessage("debug", message);
    console.debug(formatted);
    await this.writeToFile(formatted);
  }
}

export class RetryHandler {
  static async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000,
    logger?: Logger
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        if (logger) {
          await logger.warn(
            `Attempt ${attempt}/${maxRetries} failed: ${lastError.message}`
          );
        }

        if (attempt === maxRetries) {
          break;
        }

        // Exponential backoff
        const waitTime = delay * Math.pow(2, attempt - 1);
        if (logger) {
          await logger.info(`Retrying in ${waitTime}ms...`);
        }

        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }

    throw lastError!;
  }
}

export class ProgressTracker {
  private total: number;
  private current: number = 0;
  private startTime: number;
  private logger?: Logger;

  constructor(total: number, logger?: Logger) {
    this.total = total;
    this.startTime = Date.now();
    this.logger = logger;
  }

  async update(increment: number = 1): Promise<void> {
    this.current += increment;
    const percentage = Math.round((this.current / this.total) * 100);
    const elapsed = Date.now() - this.startTime;
    const rate = this.current / (elapsed / 1000);
    const eta = this.current > 0 ? (this.total - this.current) / rate : 0;

    const message =
      `Progress: ${this.current}/${this.total} (${percentage}%) - ` +
      `Rate: ${rate.toFixed(2)}/s - ETA: ${this.formatTime(eta)}`;

    if (this.logger) {
      await this.logger.info(message);
    } else {
      console.log(message);
    }
  }

  private formatTime(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  isComplete(): boolean {
    return this.current >= this.total;
  }
}

export class FileUtils {
  static async ensureDirectory(dirPath: string): Promise<void> {
    try {
      await fs.access(dirPath);
    } catch {
      await fs.mkdir(dirPath, { recursive: true });
    }
  }

  static async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  static async getFileSize(filePath: string): Promise<number> {
    try {
      const stats = await fs.stat(filePath);
      return stats.size;
    } catch {
      return 0;
    }
  }

  static sanitizeFilename(filename: string): string {
    return filename
      .replace(/[<>:"/\\|?*]/g, "-") // replace invalid characters
      .replace(/\s+/g, "-") // replace spaces with hyphens
      .replace(/-+/g, "-") // replace multiple hyphens with single
      .replace(/^-|-$/g, "") // remove leading/trailing hyphens
      .substring(0, 255); // limit length
  }

  static async writeJsonFile(filePath: string, data: any): Promise<void> {
    const jsonString = JSON.stringify(data, null, 2);
    await fs.writeFile(filePath, jsonString, "utf-8");
  }

  static async readJsonFile<T>(filePath: string): Promise<T> {
    const content = await fs.readFile(filePath, "utf-8");
    return JSON.parse(content) as T;
  }

  static async readFile(filePath: string): Promise<string> {
    return await fs.readFile(filePath, "utf-8");
  }

  static async readDirectory(dirPath: string): Promise<string[]> {
    return await fs.readdir(dirPath);
  }
}

export class ValidationUtils {
  static isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  static sanitizeHtml(html: string): string {
    // remove script tags and dangerous attributes
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
      .replace(/on\w+="[^"]*"/gi, "")
      .replace(/javascript:/gi, "");
  }
}
