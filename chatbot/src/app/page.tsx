import ChatBot from "./components/ChatBot";

export default function Home() {
  return (
    <div className="font-sans min-h-screen bg-gray-50">
      <div className="flex items-center justify-center min-h-screen p-8 sm:p-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            OptiBot Clone
          </h1>
        </div>
      </div>

      <ChatBot />
    </div>
  );
}
