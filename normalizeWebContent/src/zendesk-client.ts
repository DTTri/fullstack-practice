import axios, { AxiosInstance, AxiosResponse } from "axios";
import {
  ZendeskArticle,
  ZendeskSection,
  ZendeskCategory,
  ZendeskApiResponse,
} from "./types";

export class ZendeskClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(subdomain: string) {
    this.baseUrl = `https://${subdomain}/api/v2/help_center`;
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        Accept: "application/json",
        "User-Agent": "OptiSigns-Article-Scraper/1.0",
      },
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error(
          `API Error: ${error.response?.status} - ${error.response?.statusText}`
        );
        throw error;
      }
    );
  }

  async getCategories(): Promise<ZendeskCategory[]> {
    try {
      const response: AxiosResponse<ZendeskApiResponse<ZendeskCategory>> =
        await this.client.get("/categories.json");
      return response.data.categories as ZendeskCategory[];
    } catch (error) {
      console.error("Failed to fetch categories:", error);
      throw error;
    }
  }

  async getSections(categoryId?: number): Promise<ZendeskSection[]> {
    try {
      const url = categoryId
        ? `/categories/${categoryId}/sections.json`
        : "/sections.json";

      const response: AxiosResponse<ZendeskApiResponse<ZendeskSection>> =
        await this.client.get(url);
      return response.data.sections as ZendeskSection[];
    } catch (error) {
      console.error("Failed to fetch sections:", error);
      throw error;
    }
  }

  async getArticles(
    sectionId?: number,
    page: number = 1
  ): Promise<{ articles: ZendeskArticle[]; hasMore: boolean }> {
    try {
      const url = sectionId
        ? `/sections/${sectionId}/articles.json`
        : "/articles.json";

      const response: AxiosResponse<ZendeskApiResponse<ZendeskArticle>> =
        await this.client.get(url, {
          params: {
            page,
            per_page: 100,
            sort_by: "updated_at",
            sort_order: "desc",
          },
        });

      return {
        articles: response.data.articles as ZendeskArticle[],
        hasMore: response.data.next_page !== null,
      };
    } catch (error) {
      console.error("Failed to fetch articles:", error);
      throw error;
    }
  }

  async getAllArticles(maxArticles?: number): Promise<ZendeskArticle[]> {
    const allArticles: ZendeskArticle[] = [];
    let page = 1;
    let hasMore = true;

    console.log("Fetching all articles...");

    while (hasMore && (!maxArticles || allArticles.length < maxArticles)) {
      console.log(`Fetching page ${page}...`);

      const { articles, hasMore: morePages } = await this.getArticles(
        undefined,
        page
      );

      const articlesToAdd = maxArticles
        ? articles.slice(0, maxArticles - allArticles.length)
        : articles;

      allArticles.push(...articlesToAdd);
      hasMore = morePages && (!maxArticles || allArticles.length < maxArticles);
      page++;

      if (hasMore) {
        await this.delay(1000);
      }
    }

    console.log(`Fetched ${allArticles.length} articles total`);
    return allArticles;
  }

  async getArticle(articleId: number): Promise<ZendeskArticle> {
    try {
      const response: AxiosResponse<{ article: ZendeskArticle }> =
        await this.client.get(`/articles/${articleId}.json`);
      return response.data.article;
    } catch (error) {
      console.error(`Failed to fetch article ${articleId}:`, error);
      throw error;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
