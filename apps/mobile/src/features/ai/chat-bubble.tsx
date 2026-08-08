import { StyleSheet, Text, View } from 'react-native';

import type { ChatMessage } from '@/features/ai/types';

type ChatBubbleProps = {
  message: ChatMessage;
};

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.row, isUser && styles.userRow]}>
      {!isUser && (
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>AI</Text>
        </View>
      )}
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.content, isUser && styles.userContent]}>{message.content}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    marginBottom: 14,
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  avatar: {
    width: 30,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 15,
    backgroundColor: '#D9F1E8',
  },
  avatarText: {
    color: '#16775A',
    fontSize: 10,
    fontWeight: '800',
  },
  bubble: {
    maxWidth: '82%',
    paddingHorizontal: 15,
    paddingVertical: 11,
    borderRadius: 18,
  },
  assistantBubble: {
    borderBottomLeftRadius: 5,
    backgroundColor: '#FFFFFF',
  },
  userBubble: {
    borderBottomRightRadius: 5,
    backgroundColor: '#16775A',
  },
  content: {
    color: '#29483F',
    fontSize: 15,
    lineHeight: 22,
  },
  userContent: {
    color: '#FFFFFF',
  },
});
