import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    console.log("Received message:", message);
    console.log("API Key exists:", !!process.env.OPENAI_API_KEY);
    console.log("API Key length:", process.env.OPENAI_API_KEY?.length);
    console.log(
      "API Key starts with:",
      process.env.OPENAI_API_KEY?.substring(0, 10)
    );

    if (!message) {
      return NextResponse.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    if (!process.env.OPENAI_API_KEY) {
      console.log("No API key found");
      return NextResponse.json(
        {
          message:
            "I'm sorry, the AI service is not configured. Please contact our support team directly at support@optisigns.com or call (832) 410-8132.",
        },
        { status: 200 }
      );
    }

    // prompt
    const systemPrompt = `You are OptiBot, a helpful customer support assistant for OptiSigns, a digital signage software company. 

Key information about OptiSigns:
- OptiSigns is a cloud-based digital signage software platform
- They offer hardware players, content management, apps/integrations, and scheduling
- Popular features include weather apps, split screens, screen zones, layouts, and caching
- They have Android players, Pro players, and support various devices
- Support team is available Mon-Fri 9AM-5PM CDT at (832) 410-8132 or support@optisigns.com
- They offer a 14-day free trial
- Common use cases include retail, restaurants, corporate offices, healthcare, education

Guidelines:
- Be helpful, friendly, and professional
- Keep responses concise but informative
- If you don't know something specific, direct users to contact support
- Focus on OptiSigns-related topics
- Suggest relevant features or solutions when appropriate
- If asked about competitors, politely redirect to OptiSigns benefits`;

    const getMockResponse = (userMessage: string) => {
      const lowerMessage = userMessage.toLowerCase();

      if (lowerMessage.includes("weather")) {
        return "The Weather app is one of our most popular integrations! You can easily add live weather information to your digital signs. Simply go to Apps & Integrations in your dashboard, search for 'Weather', and configure it with your location. It updates automatically!";
      }

      if (
        lowerMessage.includes("getting started") ||
        lowerMessage.includes("guide")
      ) {
        return "Great! To get started with OptiSigns: 1) Sign up for your free 14-day trial, 2) Download the OptiSigns player app on your device, 3) Create your first content using our designer tool, 4) Assign content to your screen. Need help? Contact our team at support@optisigns.com!";
      }

      if (
        lowerMessage.includes("split screen") ||
        lowerMessage.includes("layout") ||
        lowerMessage.includes("zone")
      ) {
        return "Split screens let you display multiple content zones on one display! You can create layouts with 2, 3, or 4 zones, each showing different content like videos, images, apps, or feeds. Perfect for showing menus, promotions, and live data simultaneously.";
      }

      if (
        lowerMessage.includes("order") ||
        lowerMessage.includes("device") ||
        lowerMessage.includes("hardware")
      ) {
        return "You can order OptiSigns hardware directly from our website! We offer Android Sticks ($79.99), Pro Players ($299.99), and ProMax Players ($599.99). Free shipping available, and the Android Stick is free with yearly subscriptions!";
      }

      if (lowerMessage.includes("caching")) {
        return "OptiSigns uses smart caching to ensure your content plays smoothly even with poor internet. Content is downloaded and stored locally on your player, so your displays keep running even if connectivity is interrupted.";
      }

      if (lowerMessage.includes("pricing") || lowerMessage.includes("cost")) {
        return "OptiSigns offers flexible pricing starting with a 14-day free trial. Our plans scale with your needs, and we offer discounts for annual subscriptions. Contact our sales team at (832) 410-8132 for custom pricing!";
      }

      return "I'd be happy to help you with OptiSigns! For specific questions about our digital signage platform, features, or setup, please contact our support team at support@optisigns.com or call (832) 410-8132. We're here Mon-Fri 9AM-5PM CDT!";
    };

    try {
      const completion = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: message },
        ],
        max_tokens: 300,
        temperature: 0.7,
      });

      const aiResponse = completion.choices[0]?.message?.content;
      if (aiResponse) {
        return NextResponse.json({ message: aiResponse });
      }
    } catch (apiError) {
      console.log(
        "OpenAI API unavailable (quota/billing), using mock response:",
        apiError instanceof Error ? apiError.message : "Unknown error"
      );
    }

    // fallback to mock response
    const mockResponse = getMockResponse(message);
    return NextResponse.json({ message: mockResponse });
  } catch (error) {
    console.error("OpenAI API error:", error);
    console.error("Error details:", {
      message: error instanceof Error ? error.message : "Unknown error",
      stack: error instanceof Error ? error.stack : undefined,
      name: error instanceof Error ? error.name : undefined,
    });

    return NextResponse.json({
      message:
        "I'm experiencing some technical difficulties right now. For immediate assistance, please contact our support team at support@optisigns.com or call (832) 410-8132. Our team is available Mon-Fri 9AM-5PM CDT.",
    });
  }
}
