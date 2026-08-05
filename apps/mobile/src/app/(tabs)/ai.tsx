import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChatBubble } from '@/features/ai/chat-bubble';
import { sendChatMessage } from '@/features/ai/chat-service';
import type { ChatMessage, ChatRequest, ChatResponse } from '@/features/ai/types';

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content:
      'Chào bạn! Mình là TravelMate AI. Hãy hỏi mình về lịch trình, địa điểm, chỗ ở hoặc ngân sách chuyến đi.',
  },
];

const initialSuggestions = [
  'Lên lịch trình Đà Nẵng 3 ngày',
  'Tìm chỗ ở gần biển',
  'Ngân sách 5 triệu nên chia thế nào?',
];

function createMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
  };
}

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    if (error.response?.data.detail) {
      return error.response.data.detail;
    }
    if (error.code === 'ECONNABORTED') {
      return 'AI phản hồi quá lâu. Hãy thử lại sau.';
    }
  }
  return 'Không kết nối được AI Service. Kiểm tra URL, Wi-Fi và FastAPI.';
}

export default function AiScreen() {
  const listRef = useRef<FlatList<ChatMessage>>(null);
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [destination, setDestination] = useState('');
  const [budget, setBudget] = useState('');
  const [numPeople, setNumPeople] = useState('');
  const [suggestions, setSuggestions] = useState(initialSuggestions);
  const [provider, setProvider] = useState<ChatResponse['provider'] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (response) => {
      setMessages((current) => [...current, createMessage('assistant', response.reply)]);
      setSuggestions(response.suggestedQuestions);
      setProvider(response.provider);
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(getErrorMessage(error));
    },
  });

  const providerLabel = useMemo(() => {
    if (provider === 'gemini') return 'Gemini API';
    if (provider === 'local') return 'Qwen local';
    if (provider === 'mock') return 'Mock API';
    return 'Chưa kết nối';
  }, [provider]);

  function sendMessage(value = input) {
    const content = value.trim();
    if (!content || mutation.isPending) return;

    const destinationValue = destination.trim();
    const budgetValue = budget ? Number(budget) : undefined;
    const numPeopleValue = numPeople ? Number(numPeople) : undefined;
    const hasTripContext = Boolean(destinationValue || budgetValue || numPeopleValue);
    const request: ChatRequest = {
      message: content,
      history: messages.slice(-10).map(({ role, content: historyContent }) => ({
        role,
        content: historyContent,
      })),
      tripContext: hasTripContext
        ? {
            destination: destinationValue || undefined,
            budgetVnd: budgetValue,
            numPeople: numPeopleValue,
          }
        : undefined,
    };

    setMessages((current) => [...current, createMessage('user', content)]);
    setInput('');
    setErrorMessage(null);
    mutation.mutate(request);
  }

  function resetChat() {
    setMessages(initialMessages);
    setDestination('');
    setBudget('');
    setNumPeople('');
    setSuggestions(initialSuggestions);
    setProvider(null);
    setErrorMessage(null);
    mutation.reset();
  }

  return (
    <SafeAreaView edges={['bottom']} style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
        <View style={[styles.header, styles.desktopContent]}>
          <View>
            <Text style={styles.eyebrow}>TRAVELMATE LAB</Text>
            <Text style={styles.title}>Thử chatbot</Text>
          </View>
          <View style={styles.headerActions}>
            <View style={styles.providerBadge}>
              <View style={[styles.statusDot, provider && styles.statusDotConnected]} />
              <Text style={styles.providerText}>{providerLabel}</Text>
            </View>
            <Pressable accessibilityRole="button" onPress={resetChat} style={styles.resetButton}>
              <Text style={styles.resetText}>Đặt lại</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.contextCard}>
          <Text style={styles.contextTitle}>Ngữ cảnh thử nghiệm</Text>
          <View style={styles.contextRow}>
            <View style={styles.destinationField}>
              <Text style={styles.fieldLabel}>Điểm đến</Text>
              <TextInput
                value={destination}
                onChangeText={setDestination}
                placeholder="Đà Nẵng"
                style={styles.contextInput}
              />
            </View>
            <View style={styles.smallField}>
              <Text style={styles.fieldLabel}>Số người</Text>
              <TextInput
                value={numPeople}
                onChangeText={setNumPeople}
                keyboardType="number-pad"
                placeholder="2"
                style={styles.contextInput}
              />
            </View>
          </View>
          <Text style={styles.fieldLabel}>Ngân sách (VND)</Text>
          <TextInput
            value={budget}
            onChangeText={setBudget}
            keyboardType="number-pad"
            placeholder="5000000"
            style={styles.contextInput}
          />
        </View>

        <FlatList
          ref={listRef}
          style={styles.desktopContent}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <ChatBubble message={item} />}
          contentContainerStyle={styles.messageList}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          ListFooterComponent={
            mutation.isPending ? (
              <View style={styles.typingRow}>
                <ActivityIndicator color="#16775A" size="small" />
                <Text style={styles.typingText}>TravelMate đang trả lời...</Text>
              </View>
            ) : null
          }
        />

        <View style={[styles.composerArea, styles.desktopContent]}>
          {errorMessage && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          <FlatList
            horizontal
            data={suggestions}
            keyExtractor={(item) => item}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.suggestionList}
            renderItem={({ item }) => (
              <Pressable
                accessibilityRole="button"
                disabled={mutation.isPending}
                onPress={() => sendMessage(item)}
                style={styles.suggestionChip}>
                <Text style={styles.suggestionText}>{item}</Text>
              </Pressable>
            )}
          />

          <View style={styles.composer}>
            <TextInput
              value={input}
              onChangeText={setInput}
              editable={!mutation.isPending}
              multiline
              maxLength={1000}
              placeholder="Hỏi về chuyến đi của bạn..."
              placeholderTextColor="#81968F"
              style={styles.messageInput}
            />
            <Pressable
              accessibilityLabel="Gửi tin nhắn"
              accessibilityRole="button"
              disabled={!input.trim() || mutation.isPending}
              onPress={() => sendMessage()}
              style={({ pressed }) => [
                styles.sendButton,
                (!input.trim() || mutation.isPending) && styles.sendButtonDisabled,
                pressed && styles.sendButtonPressed,
              ]}>
              <Text style={styles.sendText}>Gửi</Text>
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F4FAF7',
  },
  container: {
    flex: 1,
  },
  desktopContent: {
    width: '100%',
    maxWidth: 920,
    alignSelf: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingTop: 14,
    paddingBottom: 12,
  },
  eyebrow: {
    color: '#16775A',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  title: {
    marginTop: 2,
    color: '#17352D',
    fontSize: 24,
    fontWeight: '800',
  },
  headerActions: {
    alignItems: 'flex-end',
    gap: 6,
  },
  providerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#E7F2EE',
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#9DACA7',
  },
  statusDotConnected: {
    backgroundColor: '#21A179',
  },
  providerText: {
    color: '#48645C',
    fontSize: 11,
    fontWeight: '700',
  },
  resetButton: {
    paddingHorizontal: 4,
  },
  resetText: {
    color: '#647B74',
    fontSize: 11,
    fontWeight: '600',
  },
  contextCard: {
    gap: 7,
    marginHorizontal: 18,
    marginBottom: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#DDEAE5',
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  contextTitle: {
    color: '#29483F',
    fontSize: 13,
    fontWeight: '800',
  },
  contextRow: {
    flexDirection: 'row',
    gap: 10,
  },
  destinationField: {
    flex: 1,
  },
  smallField: {
    width: 82,
  },
  fieldLabel: {
    marginBottom: 4,
    color: '#6E837C',
    fontSize: 10,
    fontWeight: '700',
  },
  contextInput: {
    minHeight: 36,
    paddingHorizontal: 10,
    borderRadius: 10,
    backgroundColor: '#F3F7F5',
    color: '#17352D',
    fontSize: 13,
  },
  messageList: {
    flexGrow: 1,
    justifyContent: 'flex-end',
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 8,
  },
  typingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 38,
    marginBottom: 10,
  },
  typingText: {
    color: '#6E837C',
    fontSize: 12,
  },
  composerArea: {
    borderTopWidth: 1,
    borderTopColor: '#DFEAE6',
    backgroundColor: '#FFFFFF',
  },
  errorBox: {
    marginHorizontal: 16,
    marginTop: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 10,
    backgroundColor: '#FFF0EF',
  },
  errorText: {
    color: '#A23D35',
    fontSize: 12,
    lineHeight: 17,
  },
  suggestionList: {
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 10,
  },
  suggestionChip: {
    maxWidth: 230,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#B9D9CD',
    borderRadius: 20,
    backgroundColor: '#F4FAF7',
  },
  suggestionText: {
    color: '#16775A',
    fontSize: 12,
    fontWeight: '600',
  },
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
    padding: 12,
  },
  messageInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 110,
    paddingHorizontal: 14,
    paddingTop: 11,
    paddingBottom: 11,
    borderWidth: 1,
    borderColor: '#D5E2DD',
    borderRadius: 16,
    backgroundColor: '#F8FAF9',
    color: '#17352D',
    fontSize: 15,
    lineHeight: 21,
  },
  sendButton: {
    minWidth: 58,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    backgroundColor: '#16775A',
  },
  sendButtonDisabled: {
    backgroundColor: '#AFC8BF',
  },
  sendButtonPressed: {
    opacity: 0.8,
  },
  sendText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
});
