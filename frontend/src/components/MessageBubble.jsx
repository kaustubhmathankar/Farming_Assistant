import {
  Bot,
  Check,
  Copy,
  UserRound,
  Volume2,
} from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import SourceList from "./SourceList";


export default function MessageBubble({
  message,
  languageCode = "mr",
}) {
  const effectiveLanguage =
    message.detected_language ||
    message.language ||
    languageCode;


  const [copied, setCopied] =
    useState(false);


  const isUser =
    message.role === "user";


  const userContent = String(
    message.content || ""
  );


  const hasImage = Boolean(
    message.image_preview_url
  );


  /*
   * Do not display the technical backend
   * placeholder when the user sends only an image.
   */
  const isDefaultImagePrompt =
    message.input_type ===
      "image" &&
    userContent
      .trim()
      .toLowerCase() ===
      "please check this crop image.";


  const speak = () => {
    if (
      !window.speechSynthesis
    ) {
      return;
    }


    window.speechSynthesis.cancel();


    const utterance =
      new SpeechSynthesisUtterance(
        message.content || ""
      );


    utterance.lang =
      {
        en: "en-IN",
        hi: "hi-IN",
        mr: "mr-IN",
      }[effectiveLanguage] ||
      "mr-IN";


    window.speechSynthesis.speak(
      utterance
    );
  };


  const copy = async () => {
    try {
      await navigator.clipboard?.writeText(
        message.content || ""
      );


      setCopied(true);


      window.setTimeout(
        () =>
          setCopied(false),
        1200
      );
    } catch {
      // Clipboard may be unavailable.
    }
  };


  return (
    <article
      className={`message-row ${
        isUser
          ? "user"
          : "assistant"
      }`}
    >
      <div className="message-stack">
        <div className="message-role-label">
          <div className="avatar message-avatar">
            {isUser ? (
              <UserRound size={16} />
            ) : (
              <Bot size={17} />
            )}
          </div>

          <span>
            {isUser
              ? "You"
              : "KrishiSaathi"}
          </span>
        </div>


        <div className="message-bubble">
          {isUser ? (
            <>
              {hasImage && (
                <div className="sent-image-wrap">
                  <img
                    src={
                      message.image_preview_url
                    }
                    alt={
                      message.image_name ||
                      "Attached crop"
                    }
                    className="sent-image"
                    loading="lazy"
                  />

                  {message.image_name && (
                    <span className="sent-image-name">
                      {
                        message.image_name
                      }
                    </span>
                  )}
                </div>
              )}


              {(
                !isDefaultImagePrompt ||
                !hasImage
              ) &&
                userContent && (
                  <p className="user-message-text">
                    {
                      userContent
                    }
                  </p>
                )}
            </>
          ) : (
            <div className="assistant-markdown">
              <ReactMarkdown
                remarkPlugins={[
                  remarkGfm,
                ]}
                components={{
                  a: ({
                    children,
                    href,
                  }) => (
                    <a
                      href={
                        href
                      }
                      target="_blank"
                      rel="noreferrer"
                    >
                      {
                        children
                      }
                    </a>
                  ),
                }}
              >
                {
                  message.content ||
                  ""
                }
              </ReactMarkdown>
            </div>
          )}
        </div>


        {!isUser && (
          <div className="message-actions">
            <button
              type="button"
              onClick={speak}
            >
              <Volume2 size={14} />
              Listen
            </button>

            <button
              type="button"
              onClick={
                copy
              }
            >
              {copied ? (
                <Check size={14} />
              ) : (
                <Copy size={14} />
              )}

              {copied
                ? "Copied"
                : "Copy"}
            </button>
          </div>
        )}


        {!isUser && (
          <SourceList
            sources={
              message.sources ||
              []
            }
          />
        )}
      </div>
    </article>
  );
}