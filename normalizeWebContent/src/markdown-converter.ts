import TurndownService from "turndown";
import * as cheerio from "cheerio";

export class MarkdownConverter {
  private turndownService: TurndownService;

  constructor() {
    this.turndownService = new TurndownService({
      headingStyle: "atx",
      hr: "---",
      bulletListMarker: "-",
      codeBlockStyle: "fenced",
      fence: "```",
      emDelimiter: "*",
      strongDelimiter: "**",
      linkStyle: "inlined",
      linkReferenceStyle: "full",
    });

    this.setupCustomRules();
  }

  private setupCustomRules(): void {
    this.turndownService.addRule("codeBlocks", {
      filter: ["pre"],
      replacement: (content, node) => {
        const codeElement = node.querySelector("code");
        if (codeElement) {
          const className = codeElement.getAttribute("class") || "";
          const languageMatch = className.match(/language-(\w+)/);
          const language = languageMatch ? languageMatch[1] : "";

          return `\n\n\`\`\`${language}\n${
            codeElement.textContent || ""
          }\n\`\`\`\n\n`;
        }
        return `\n\n\`\`\`\n${content}\n\`\`\`\n\n`;
      },
    });

    this.turndownService.addRule("inlineCode", {
      filter: ["code"],
      replacement: (content) => {
        return `\`${content}\``;
      },
    });

    this.turndownService.addRule("tables", {
      filter: "table",
      replacement: (content, node) => {
        return this.convertTable(node as any);
      },
    });

    this.turndownService.addRule("images", {
      filter: "img",
      replacement: (content, node) => {
        const alt = node.getAttribute("alt") || "";
        const src = node.getAttribute("src") || "";
        const title = node.getAttribute("title");

        if (title) {
          return `![${alt}](${src} "${title}")`;
        }
        return `![${alt}](${src})`;
      },
    });

    this.turndownService.addRule("blockquotes", {
      filter: "blockquote",
      replacement: (content) => {
        return content.replace(/^/gm, "> ").replace(/^> $/gm, ">");
      },
    });

    this.turndownService.addRule("removeUnwanted", {
      filter: [
        "nav",
        "header",
        "footer",
        ".navigation",
        ".breadcrumb",
        ".sidebar",
        ".ads",
        ".advertisement",
      ],
      replacement: () => "",
    });
  }

  private convertTable(table: any): string {
    const $ = cheerio.load(table.outerHTML);
    const rows: string[] = [];

    const headerCells = $("thead tr th, tr:first-child td")
      .map((_, cell) => {
        return $(cell).text().trim();
      })
      .get();

    if (headerCells.length > 0) {
      rows.push(`| ${headerCells.join(" | ")} |`);
      rows.push(`| ${headerCells.map(() => "---").join(" | ")} |`);
    }
    $("tbody tr, tr:not(:first-child)").each((_, row) => {
      const cells = $(row)
        .find("td")
        .map((_, cell) => {
          return $(cell).text().trim();
        })
        .get();

      if (cells.length > 0) {
        rows.push(`| ${cells.join(" | ")} |`);
      }
    });

    return rows.length > 0 ? `\n\n${rows.join("\n")}\n\n` : "";
  }

  convertHtmlToMarkdown(html: string, baseUrl?: string): string {
    const cleanedHtml = this.cleanHtml(html, baseUrl);
    let markdown = this.turndownService.turndown(cleanedHtml);
    markdown = this.postProcessMarkdown(markdown);
    return markdown;
  }

  private cleanHtml(html: string, baseUrl?: string): string {
    const $ = cheerio.load(html);

    $(
      "script, style, nav, header, footer, .navigation, .breadcrumb, .sidebar, .ads, .advertisement"
    ).remove();

    $("p:empty").remove();

    if (baseUrl) {
      $('a[href^="/"]').each((_, element) => {
        const href = $(element).attr("href");
        if (href) {
          $(element).attr("href", new URL(href, baseUrl).toString());
        }
      });

      $('img[src^="/"]').each((_, element) => {
        const src = $(element).attr("src");
        if (src) {
          $(element).attr("src", new URL(src, baseUrl).toString());
        }
      });
    }

    $("*").each((_, element) => {
      if (element.type === "text") {
        element.data = element.data.replace(/\s+/g, " ");
      }
    });

    return $.html();
  }

  private postProcessMarkdown(markdown: string): string {
    // remove  blank lines
    markdown = markdown.replace(/\n{3,}/g, "\n\n");
    // clean up list formatting
    markdown = markdown.replace(/^(\s*)-\s*$/gm, "");

    // fix spacing around headers
    markdown = markdown.replace(/^(#{1,6})\s*(.+)$/gm, "$1 $2");
    // Ensure proper spacing around code blocks
    markdown = markdown.replace(/```(\w*)\n/g, "```$1\n");
    // clean up trailing whitespace
    markdown = markdown.replace(/[ \t]+$/gm, "");
    // ensure file ends with single newline
    markdown = markdown.trim() + "\n";
    return markdown;
  }

  createSlug(title: string): string {
    return title
      .toLowerCase()
      .replace(/[^\w\s-]/g, "") // remove special characters
      .replace(/\s+/g, "-") // Replace spaces with hyphens
      .replace(/-+/g, "-") // replace multiple hyphens with single
      .replace(/^-|-$/g, ""); // remove leading/trailing hyphens
  }
}
