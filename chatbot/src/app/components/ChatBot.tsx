"use client";

import React, { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  isClickable?: boolean;
  questionText?: string;
  questions?: string[];
}

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: 'Hi, I\'m OptiBot, here to help with OptiSigns questions like "Weather app" or "How caching works."',
      isBot: true,
    },
    {
      id: "2",
      text: "Here are some common questions I can help you with:\n• Getting Started Guide\n• Split Screens, Screen Zones, Layout\n• Order a Device",
      isBot: true,
      isClickable: true,
      questions: [
        "Getting Started Guide",
        "Split Screens, Screen Zones, Layout",
        "Order a Device",
      ],
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevent page reload
    if (!inputText.trim() || isLoading) return;

    sendMessage(inputText.trim());
  };

  const sendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: text,
      isBot: false,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // Call OpenAI API
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.message,
        isBot: true,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm sorry, I'm having trouble connecting right now. Please try again later or contact our support team directly at support@optisigns.com or call (832) 410-8132.",
        isBot: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionClick = (question: string) => {
    sendMessage(question);
  };

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg transition-all duration-300 z-50 flex items-center justify-center ${
          isOpen
            ? "bg-gray-600 hover:bg-gray-700"
            : "bg-green-500 hover:bg-green-600"
        }`}
      >
        {isOpen ? (
          <span className="text-white text-xl">×</span>
        ) : (
          <span className="text-white text-xl">💬</span>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl z-40 flex flex-col">
          <div className="bg-green-500 text-white p-4 rounded-t-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div>
                  <h3 className="font-semibold">Contact Support Team</h3>
                  <p className="text-xs opacity-90 mt-2">
                    Have a problem? Call our Houston team!
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center mt-2">
              <div className="flex flex-col items-center">
                <div className="flex items-center justify-center bg-white rounded-2xl py-0.5 px-4">
                  <span className="text-center mx-auto text-green-500 text-xs">
                    (832) 410-8132
                  </span>
                </div>
                <div className="flex items-center text-xs">
                  <span>Mon - Fri: 9AM - 5PM CDT</span>
                </div>
              </div>
              <div className="flex flex-col items-center">
                <div className="flex items-center justify-center bg-white rounded-2xl py-0.5 px-4">
                  <span className="text-center mx-auto text-green-500 text-xs">
                    support@optisigns.com
                  </span>
                </div>
                <div className="flex items-center text-xs">
                  <span>Mon - Fri: 7AM - 7PM CDT</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.isBot ? "justify-start" : "justify-end"
                }`}
              >
                {message.isBot && (
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-2 flex-shrink-0 mt-1">
                    <span className="text-white text-xs font-bold">O</span>
                  </div>
                )}
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.isBot
                      ? message.isClickable
                        ? "bg-gray-100 text-gray-800 border border-green-200"
                        : "bg-gray-100 text-gray-800"
                      : "bg-green-500 text-white"
                  }`}
                >
                  {message.questions ? (
                    <div className="text-sm">
                      <p className="mb-2">
                        Here are some common questions I can help you with:
                      </p>
                      {message.questions.map((question, index) => (
                        <div
                          key={index}
                          className="text-green-600 hover:text-green-700 hover:underline cursor-pointer py-1"
                          onClick={() => handleQuestionClick(question)}
                        >
                          • {question}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm">{message.text}</p>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-3 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form
            onSubmit={handleSubmit}
            className="p-2 border-t border-gray-200"
          >
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your message here..."
                className="flex-1 p-2 rounded-lg focus:outline-none focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputText.trim()}
                className="p-2 rounded-2xl hover:bg-gray-200"
              >
                <span className="text-gray-500">➤</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
