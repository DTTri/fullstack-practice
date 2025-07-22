import * as fs from "fs/promises";
import * as path from "path";
import { ZendeskClient } from "./zendesk-client";
import { MarkdownConverter } from "./markdown-converter";
import {
  ZendeskArticle,
  ZendeskSection,
  ZendeskCategory,
  ProcessedArticle,
  ScrapingConfig,
} from "./types";

export class ArticleScraper {
  private zendeskClient: ZendeskClient;
  private markdownConverter: MarkdownConverter;
  private config: ScrapingConfig;
  private categories: Map<number, ZendeskCategory> = new Map();
  private sections: Map<number, ZendeskSection> = new Map();

  constructor(config: ScrapingConfig) {
    this.config = config;
    this.zendeskClient = new ZendeskClient("support.optisigns.com");
    this.markdownConverter = new MarkdownConverter();
  }

  async initialize(): Promise<void> {
    console.log("Initializing scraper...");

    await this.ensureOutputDirectory();
    await this.loadCategoriesAndSections();
    console.log(
      `Loaded ${this.categories.size} categories and ${this.sections.size} sections`
    );
  }

  private async ensureOutputDirectory(): Promise<void> {
    try {
      await fs.access(this.config.outputDir);
    } catch {
      await fs.mkdir(this.config.outputDir, { recursive: true });
      console.log(`Created output directory: ${this.config.outputDir}`);
    }
  }

  private async loadCategoriesAndSections(): Promise<void> {
    try {
      const categories = await this.zendeskClient.getCategories();
      categories.forEach((category) => {
        this.categories.set(category.id, category);
      });
      const sections = await this.zendeskClient.getSections();
      sections.forEach((section) => {
        this.sections.set(section.id, section);
      });
    } catch (error) {
      console.error("Failed to load categories and sections:", error);
      throw error;
    }
  }

  async scrapeArticles(): Promise<ProcessedArticle[]> {
    console.log("Starting article scraping...");

    const articles = await this.zendeskClient.getAllArticles(
      this.config.maxArticles
    );
    const processedArticles: ProcessedArticle[] = [];

    console.log(`Processing ${articles.length} articles...`);

    for (let i = 0; i < articles.length; i++) {
      const article = articles[i];
      console.log(
        `Processing article ${i + 1}/${articles.length}: ${article.title}`
      );

      try {
        const processedArticle = await this.processArticle(article);
        await this.saveArticle(processedArticle);
        processedArticles.push(processedArticle);

        // add a little delay between requests
        if (this.config.delay && i < articles.length - 1) {
          await this.delay(this.config.delay);
        }
      } catch (error) {
        console.error(
          `Failed to process article ${article.id} (${article.title}):`,
          error
        );

        continue;
      }
    }

    console.log(`Successfully processed ${processedArticles.length} articles`);
    return processedArticles;
  }

  private async processArticle(
    article: ZendeskArticle
  ): Promise<ProcessedArticle> {
    const section = this.sections.get(article.section_id);
    const category = section
      ? this.categories.get(section.category_id)
      : undefined;

    const markdownContent = this.markdownConverter.convertHtmlToMarkdown(
      article.body,
      this.config.baseUrl
    );
    const slug = this.markdownConverter.createSlug(article.title);
    const frontMatter = this.createFrontMatter(article, section, category);
    const fullContent = `${frontMatter}\n\n${markdownContent}`;

    return {
      id: article.id,
      title: article.title,
      slug,
      content: fullContent,
      url: article.html_url,
      category: category?.name || "Unknown",
      section: section?.name || "Unknown",
      createdAt: article.created_at,
      updatedAt: article.updated_at,
    };
  }

  private createFrontMatter(
    article: ZendeskArticle,
    section?: ZendeskSection,
    category?: ZendeskCategory
  ): string {
    const frontMatter = [
      "---",
      `title: "${article.title.replace(/"/g, '\\"')}"`,
      `id: ${article.id}`,
      `url: ${article.html_url}`,
      `category: "${category?.name || "Unknown"}"`,
      `section: "${section?.name || "Unknown"}"`,
      `created_at: ${article.created_at}`,
      `updated_at: ${article.updated_at}`,
      `vote_sum: ${article.vote_sum}`,
      `vote_count: ${article.vote_count}`,
      "---",
    ];

    return frontMatter.join("\n");
  }

  private async saveArticle(article: ProcessedArticle): Promise<void> {
    const filename = `${article.slug}.md`;
    const filepath = path.join(this.config.outputDir, filename);

    try {
      await fs.writeFile(filepath, article.content, "utf-8");
      console.log(`Saved: ${filename}`);
    } catch (error) {
      console.error(`Failed to save article ${article.slug}:`, error);
      throw error;
    }
  }

  async generateIndex(articles: ProcessedArticle[]): Promise<void> {
    console.log("Generating index file...");

    const indexContent = this.createIndexContent(articles);
    const indexPath = path.join(this.config.outputDir, "INDEX.md");

    try {
      await fs.writeFile(indexPath, indexContent, "utf-8");
      console.log("Generated INDEX.md");
    } catch (error) {
      console.error("Failed to generate index:", error);
      throw error;
    }
  }

  private createIndexContent(articles: ProcessedArticle[]): string {
    const lines = [
      "# OptiSigns Support Articles Index",
      "",
      `Generated on: ${new Date().toISOString()}`,
      `Total articles: ${articles.length}`,
      "",
      "## Articles by Category",
      "",
    ];

    // group articles by category
    const articlesByCategory = new Map<string, ProcessedArticle[]>();
    articles.forEach((article) => {
      const category = article.category;
      if (!articlesByCategory.has(category)) {
        articlesByCategory.set(category, []);
      }
      articlesByCategory.get(category)!.push(article);
    });
    const sortedCategories = Array.from(articlesByCategory.keys()).sort();

    sortedCategories.forEach((category) => {
      lines.push(`### ${category}`);
      lines.push("");

      const categoryArticles = articlesByCategory
        .get(category)!
        .sort((a, b) => a.title.localeCompare(b.title));

      categoryArticles.forEach((article) => {
        lines.push(
          `- [${article.title}](${article.slug}.md) (ID: ${article.id})`
        );
      });

      lines.push("");
    });

    return lines.join("\n");
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
