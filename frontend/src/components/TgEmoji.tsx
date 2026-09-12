import React from 'react';

// Safe Emoji detection without failing on older WebViews
const HAS_EMOJI_SUPPORT = (() => {
  try {
    new RegExp('\\p{Extended_Pictographic}', 'u');
    return true;
  } catch {
    return false;
  }
})();

// Telegram Style Premium Animated Emojis Dictionary (using high quality animated SVGs / WebPs / Telegram Lottie URLs)
export interface AnimatedEmojiItem {
  code: string;
  name: string;
  url: string;
  fallback: string;
}

export const TELEGRAM_ANIMATED_EMOJIS: Record<string, AnimatedEmojiItem> = {
  ':anim_fire:': {
    code: ':anim_fire:',
    name: 'Olov',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Smileys/Fire.webp',
    fallback: '🔥',
  },
  ':anim_heart:': {
    code: ':anim_heart:',
    name: 'Yurak',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Smileys/Growing%20Heart.webp',
    fallback: '❤️',
  },
  ':anim_party:': {
    code: ':anim_party:',
    name: 'Bayram',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Activities/Party%20Popper.webp',
    fallback: '🎉',
  },
  ':anim_star:': {
    code: ':anim_star:',
    name: 'Yulduz',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Travel%20%26%20Places/Glowing%20Star.webp',
    fallback: '⭐',
  },
  ':anim_rocket:': {
    code: ':anim_rocket:',
    name: 'Raketa',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Travel%20%26%20Places/Rocket.webp',
    fallback: '🚀',
  },
  ':anim_crown:': {
    code: ':anim_crown:',
    name: 'Toj',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Objects/Crown.webp',
    fallback: '👑',
  },
  ':anim_gem:': {
    code: ':anim_gem:',
    name: 'Olmos',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Objects/Gem%20Stone.webp',
    fallback: '💎',
  },
  ':anim_laugh:': {
    code: ':anim_laugh:',
    name: 'Kulgi',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Smileys/Rolling%20On%20The%20Floor%20Laughing.webp',
    fallback: '🤣',
  },
  ':anim_cool:': {
    code: ':anim_cool:',
    name: 'Krosh',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Smileys/Smiling%20Face%20With%20Sunglasses.webp',
    fallback: '😎',
  },
  ':anim_100:': {
    code: ':anim_100:',
    name: '100',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/Symbols/Hundred%20Points.webp',
    fallback: '💯',
  },
  ':anim_thumbsup:': {
    code: ':anim_thumbsup:',
    name: 'Layk',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/People%20With%20Activities/Thumbs%20Up.webp',
    fallback: '👍',
  },
  ':anim_clap:': {
    code: ':anim_clap:',
    name: 'Qarsak',
    url: 'https://raw.githubusercontent.com/Tarikul-Islam-Anor/Telegram-Animated-Emojis/main/People%20With%20Activities/Clapping%20Hands.webp',
    fallback: '👏',
  },
};

function toEmojiHex(str: string): string {
  try {
    const cps: string[] = [];
    for (let i = 0; i < str.length; i++) {
      const code = str.codePointAt(i);
      if (!code) continue;
      if (code > 0xffff) i++;
      if (code !== 0xfe0f && code !== 0xfe0e) {
        cps.push(code.toString(16));
      }
    }
    return cps.join('-');
  } catch {
    return '';
  }
}

export const TgEmoji: React.FC<{ emoji: string; className?: string; size?: number | string }> = ({
  emoji,
  className = '',
  size,
}) => {
  const [loadFailed, setLoadFailed] = React.useState(false);
  const hex = toEmojiHex(emoji);

  if (!hex || loadFailed) {
    return <span className={className}>{emoji}</span>;
  }
  const url = `https://cdnjs.cloudflare.com/ajax/libs/emoji-datasource-apple/15.0.1/img/apple/64/${hex}.png`;

  return (
    <img
      src={url}
      alt={emoji}
      className={`inline-block align-[-0.15em] mx-[0.06em] select-none object-contain ${className || 'w-[1.2em] h-[1.2em]'}`}
      style={size ? { width: size, height: size } : undefined}
      loading="lazy"
      draggable={false}
      onError={() => setLoadFailed(true)}
    />
  );
};

export const TgAnimatedEmoji: React.FC<{ code: string; className?: string; size?: number | string }> = ({
  code,
  className = '',
  size,
}) => {
  const emojiData = TELEGRAM_ANIMATED_EMOJIS[code];

  if (!emojiData) {
    return <span>{code}</span>;
  }

  return (
    <img
      src={emojiData.url}
      alt={emojiData.name}
      title={emojiData.name}
      className={`inline-block align-[-0.2em] mx-[0.08em] select-none object-contain transition-transform hover:scale-125 duration-200 ${className || 'w-[1.4em] h-[1.4em]'}`}
      style={size ? { width: size, height: size } : undefined}
      loading="eager"
      draggable={false}
      onError={(e) => {
        // Fallback to text emoji if WebP fails to load
        (e.target as HTMLElement).style.display = 'none';
      }}
    />
  );
};

export const TgText: React.FC<{ children?: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => {
  if (typeof children !== 'string') {
    return <span className={className}>{children}</span>;
  }

  const text = children;
  if (!text) return null;

  // Pattern to match animated codes like :anim_fire: or standard unicode emojis
  const animRegex = /(:anim_[a-z0-9_]+:)/g;
  const parts: React.ReactNode[] = [];

  const textSegments = text.split(animRegex);

  textSegments.forEach((segment, idx) => {
    if (TELEGRAM_ANIMATED_EMOJIS[segment]) {
      parts.push(
        <TgAnimatedEmoji key={`anim-emoji-${idx}-${segment}`} code={segment} />
      );
    } else {
      if (!HAS_EMOJI_SUPPORT) {
        parts.push(segment);
        return;
      }
      try {
        const regex = new RegExp('(\\p{Extended_Pictographic}(?:\\u200D\\p{Extended_Pictographic})*)', 'gu');
        let lastIndex = 0;
        let match: RegExpExecArray | null;

        while ((match = regex.exec(segment)) !== null) {
          if (match.index > lastIndex) {
            parts.push(segment.slice(lastIndex, match.index));
          }
          const emojiChar = match[0];
          parts.push(
            <TgEmoji key={`emoji-${idx}-${match.index}-${emojiChar}`} emoji={emojiChar} />
          );
          lastIndex = regex.lastIndex;
        }

        if (lastIndex < segment.length) {
          parts.push(segment.slice(lastIndex));
        }
      } catch {
        parts.push(segment);
      }
    }
  });

  return <span className={className}>{parts}</span>;
};

