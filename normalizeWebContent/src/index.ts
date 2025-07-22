#!/usr/bin/env node

import { Command } from "commander";
import * as path from "path";
import { ArticleScraper } from "./article-scraper";
import { ScrapingConfig } from "./types";
import { Logger, FileUtils } from "./utils";
import chalk from "chalk";

const program = new Command();

program
  .name("normalize-web-content")
  .description("Scrape and normalize articles from support.optisigns.com")
  .version("1.0.0");

program
  .command("scrape")
  .description("Scrape articles from OptiSigns support site")
  .option(
    "-o, --output <dir>",
    "Output directory for markdown files",
    "./output"
  )
  .option(
    "-m, --max-articles <number>",
    "Maximum number of articles to scrape",
    "50"
  )
  .option("-d, --delay <ms>", "Delay between requests in milliseconds", "1000")
  .option(
    "-r, --retries <number>",
    "Number of retries for failed requests",
    "3"
  )
  .option("-l, --log-file <file>", "Log file path")
  .option("--no-index", "Skip generating index file")
  .action(async (options) => {
    const config: ScrapingConfig = {
      baseUrl: "https://support.optisigns.com",
      outputDir: path.resolve(options.output),
      maxArticles: parseInt(options.maxArticles),
      delay: parseInt(options.delay),
      retries: parseInt(options.retries),
    };

    const logger = new Logger(options.logFile);

    try {
      console.log(chalk.blue("Starting OptiSigns article scraper..."));
      await logger.info("Starting scraping process");

      // ensure output directory exists
      await FileUtils.ensureDirectory(config.outputDir);

      const scraper = new ArticleScraper(config);
      await scraper.initialize();
      console.log(chalk.yellow("Scraping articles..."));
      const articles = await scraper.scrapeArticles();

      if (options.index) {
        console.log(chalk.yellow(" Generating index..."));
        await scraper.generateIndex(articles);
      }

      console.log(
        chalk.green(`Successfully scraped ${articles.length} articles!`)
      );
      console.log(chalk.blue(`Output directory: ${config.outputDir}`));

      await logger.info(
        `Scraping completed successfully. ${articles.length} articles processed.`
      );
    } catch (error) {
      console.error(chalk.red("Scraping failed:"), error);
      await logger.error("Scraping failed", error as Error);
      process.exit(1);
    }
  });

program
  .command("validate")
  .description("Validate scraped markdown files")
  .option(
    "-i, --input <dir>",
    "Input directory containing markdown files",
    "./output"
  )
  .action(async (options) => {
    const inputDir = path.resolve(options.input);
    // const logger = new Logger();

    try {
      console.log(chalk.blue(" Validating markdown files..."));

      const files = await FileUtils.readDirectory(inputDir);
      const markdownFiles = files.filter((file) => file.endsWith(".md"));

      console.log(chalk.yellow(`Found ${markdownFiles.length} markdown files`));

      let validFiles = 0;
      let invalidFiles = 0;

      for (const file of markdownFiles) {
        const filePath = path.join(inputDir, file);
        try {
          const content = await FileUtils.readFile(filePath);

          // validate
          const hasTitle = content.includes("title:");
          const hasFrontMatter = content.startsWith("---");
          const hasContent = content.length > 100;

          if (hasTitle && hasFrontMatter && hasContent) {
            validFiles++;
            console.log(chalk.green(`${file}`));
          } else {
            invalidFiles++;
            console.log(chalk.red(`${file} - Missing required elements`));
          }
        } catch (error) {
          invalidFiles++;
          console.log(chalk.red(`${file} - Read error: ${error}`));
        }
      }

      console.log(chalk.blue(`\nValidation Summary:`));
      console.log(chalk.green(`Valid files: ${validFiles}`));
      console.log(chalk.red(`Invalid files: ${invalidFiles}`));
      console.log(chalk.yellow(`Total files: ${markdownFiles.length}`));
    } catch (error) {
      console.error(chalk.red("Validation failed:"), error);
      process.exit(1);
    }
  });

program
  .command("stats")
  .description("Show statistics about scraped articles")
  .option(
    "-i, --input <dir>",
    "Input directory containing markdown files",
    "./output"
  )
  .action(async (options) => {
    const inputDir = path.resolve(options.input);

    try {
      console.log(chalk.blue("Analyzing scraped articles..."));

      const indexPath = path.join(inputDir, "INDEX.md");
      const indexExists = await FileUtils.fileExists(indexPath);

      if (!indexExists) {
        console.log(chalk.red("INDEX.md not found. Run scrape command first."));
        process.exit(1);
      }

      const files = await FileUtils.readDirectory(inputDir);
      const markdownFiles = files.filter(
        (file) => file.endsWith(".md") && file !== "INDEX.md"
      );

      let totalSize = 0;
      const categories = new Map<string, number>();

      for (const file of markdownFiles) {
        const filePath = path.join(inputDir, file);
        const size = await FileUtils.getFileSize(filePath);
        totalSize += size;

        // get category from front matter
        try {
          const content = await FileUtils.readFile(filePath);
          const categoryMatch = content.match(/category: "([^"]+)"/);
          if (categoryMatch) {
            const category = categoryMatch[1];
            categories.set(category, (categories.get(category) || 0) + 1);
          }
        } catch (error) {
          // skip
        }
      }

      console.log(chalk.blue("\n Statistics:"));
      console.log(chalk.yellow(`Total articles: ${markdownFiles.length}`));
      console.log(
        chalk.yellow(`Total size: ${(totalSize / 1024).toFixed(2)} KB`)
      );
      console.log(
        chalk.yellow(
          `Average size: ${(totalSize / markdownFiles.length / 1024).toFixed(
            2
          )} KB`
        )
      );

      console.log(chalk.blue("\n Articles by category:"));
      const sortedCategories = Array.from(categories.entries()).sort(
        (a, b) => b[1] - a[1]
      );

      sortedCategories.forEach(([category, count]) => {
        console.log(chalk.green(`  ${category}: ${count} articles`));
      });
    } catch (error) {
      console.error(chalk.red(" Stats analysis failed:"), error);
      process.exit(1);
    }
  });

process.on("unhandledRejection", (reason, promise) => {
  console.error(
    chalk.red("Unhandled Rejection at:"),
    promise,
    chalk.red("reason:"),
    reason
  );
  process.exit(1);
});

process.on("uncaughtException", (error) => {
  console.error(chalk.red("Uncaught Exception:"), error);
  process.exit(1);
});

program.parse();
