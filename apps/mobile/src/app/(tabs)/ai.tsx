import { Ionicons } from '@expo/vector-icons';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Keyboard, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { AppScreen, Avatar, Brand } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { useTravel } from '@/context/TravelContext';
import { apiRequest, ChatResponse } from '@/lib/api';

type Message = { id: string; role: 'assistant' | 'user'; content: string; pending?: boolean };

const defaultPrompts = ['Gợi ý món địa phương', 'Tối ưu ngân sách', 'Lịch trình có quá dày?', 'Chuẩn bị hành lý'];
const aiServiceUrl = process.env.EXPO_PUBLIC_AI_SERVICE_URL?.replace(/\/$/, '');
type AiStatus = 'checking' | 'online' | 'offline';

export default function AiScreen() {
  const { user } = useSession();
  const { activeTrip, trips, setActiveTripId } = useTravel();
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState(defaultPrompts);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [aiStatus, setAiStatus] = useState<AiStatus>('checking');
  const listRef = useRef<FlatList<Message>>(null);

  useEffect(() => {
    let active = true;
    async function checkAiHealth() {
      if (!aiServiceUrl) {
        if (active) setAiStatus('offline');
        return;
      }
      try {
        const response = await fetch(`${aiServiceUrl}/health`);
        if (active) setAiStatus(response.ok ? 'online' : 'offline');
      } catch {
        if (active) setAiStatus('offline');
      }
    }
    checkAiHealth();
    const timer = setInterval(checkAiHealth, 15_000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const show = Keyboard.addListener(showEvent, () => {
      setKeyboardVisible(true);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    });
    const hide = Keyboard.addListener(hideEvent, () => setKeyboardVisible(false));
    return () => { show.remove(); hide.remove(); };
  }, []);

  useEffect(() => {
    setConversationId(null);
    setSuggestions(defaultPrompts);
    setMessages([{
      id: `hello-${activeTrip?.id ?? 'general'}`,
      role: 'assistant',
      content: activeTrip
        ? `Mình đang đồng hành cùng chuyến “${activeTrip.name}”. Mình đã có điểm đến ${activeTrip.destination}, thời gian ${activeTrip.durationDays} ngày và ngân sách của chuyến — bạn muốn bắt đầu từ đâu?`
        : 'Chọn một chuyến đi để mình đọc lịch trình, ngân sách và đưa ra gợi ý đúng ngữ cảnh.',
    }]);
  }, [activeTrip]);

  async function sendMessage(value = input) {
    const text = value.trim();
    if (!text || sending) return;
    const userMessage: Message = { id: `u-${Date.now()}`, role: 'user', content: text };
    const pendingId = `a-${Date.now()}`;
    setMessages((current) => [...current, userMessage, { id: pendingId, role: 'assistant', content: 'Mình đang đọc dữ liệu chuyến đi...', pending: true }]);
    setInput('');
    setSending(true);
    requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    try {
      const response = await apiRequest<ChatResponse>('/api/v1/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ conversationId, tripId: activeTrip?.id ?? null, message: text }),
      });
      setConversationId(response.conversationId);
      if (response.suggestedQuestions?.length) setSuggestions(response.suggestedQuestions);
      setMessages((current) => current.map((message) => message.id === pendingId ? { ...message, content: response.reply, pending: false } : message));
    } catch (cause) {
      setMessages((current) => current.map((message) => message.id === pendingId ? { ...message, content: cause instanceof Error ? cause.message : 'Mình chưa thể trả lời lúc này.', pending: false } : message));
    } finally {
      setSending(false);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    }
  }

  return (
    <KeyboardAvoidingView style={styles.keyboardRoot} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={0}>
      <AppScreen scroll={false} style={[styles.content, keyboardVisible && styles.contentKeyboard]}>
        <View style={styles.topbar}>
          <Brand compact />
          <View style={styles.topActions}>
            <View style={[styles.online, aiStatus === 'offline' && styles.offline]}>
              <View style={[styles.onlineDot, aiStatus === 'checking' && styles.checkingDot, aiStatus === 'offline' && styles.offlineDot]} />
              <Text style={[styles.onlineText, aiStatus === 'offline' && styles.offlineText]}>
                {aiStatus === 'online' ? 'AI online' : aiStatus === 'checking' ? 'Đang kiểm tra' : 'AI offline'}
              </Text>
            </View>
            <Avatar name={user?.fullName} size={38} />
          </View>
        </View>

        {!keyboardVisible && <View style={styles.heading}>
          <Text style={styles.eyebrow}>TRỢ LÝ HÀNH TRÌNH</Text>
          <Text style={styles.title}>Bạn muốn hỏi gì?</Text>
          <Text style={styles.subtitle}>Lịch trình, món ngon, chi phí — mình đã nối với chuyến đi hiện tại.</Text>
        </View>}

        {!keyboardVisible && trips.length > 0 && <View style={styles.tripDock}>
          <View style={styles.tripDockIcon}><Ionicons name="map" size={17} color={palette.ink} /></View>
          <ScrollView horizontal style={styles.tripScroller} contentContainerStyle={styles.tripRail} showsHorizontalScrollIndicator={false}>
            {trips.map((trip) => (
              <Pressable key={trip.id} onPress={() => setActiveTripId(trip.id)} style={[styles.tripChip, trip.id === activeTrip?.id && styles.tripChipActive]}>
                <Text style={[styles.tripChipTitle, trip.id === activeTrip?.id && styles.tripChipTitleActive]} numberOfLines={1}>{trip.destination}</Text>
                <Text style={[styles.tripChipMeta, trip.id === activeTrip?.id && styles.tripChipMetaActive]}>{trip.durationDays} ngày</Text>
              </Pressable>
            ))}
          </ScrollView>
          <Ionicons name="chevron-forward" size={16} color={palette.muted} />
        </View>}

        <View style={styles.chatShell}>
        <View style={styles.chatCard}>
          <View style={[styles.chatTop, keyboardVisible && styles.chatTopKeyboard]}>
            <View style={styles.aiAvatar}><Ionicons name="sparkles" size={19} color={palette.ink} /></View>
            <View style={styles.chatIdentity}>
              <Text style={styles.chatName}>TravelMate AI</Text>
              <Text style={styles.chatContext}>{activeTrip ? `${activeTrip.name} • ${activeTrip.destination}` : 'Trợ lý du lịch cá nhân'}</Text>
            </View>
            <View style={styles.contextBadge}><Ionicons name="link" size={13} color={palette.forest} /><Text style={styles.contextBadgeText}>Đã nối dữ liệu</Text></View>
          </View>

          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(item) => item.id}
            style={styles.messageListFrame}
            contentContainerStyle={styles.messageList}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
            renderItem={({ item }) => (
              <View style={[styles.messageRow, item.role === 'user' && styles.messageRowUser]}>
                {item.role === 'assistant' && <View style={styles.miniAvatar}><Ionicons name="sparkles" size={12} color={palette.white} /></View>}
                <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
                  <Text style={styles.bubbleText}>{item.content}</Text>
                  {item.pending && <View style={styles.typing}><ActivityIndicator size="small" color={palette.forest} /><Text style={styles.typingText}>Đang suy nghĩ</Text></View>}
                </View>
              </View>
            )}
          />

          {!keyboardVisible && <ScrollView horizontal style={styles.promptScroller} contentContainerStyle={styles.promptRail} showsHorizontalScrollIndicator={false} keyboardShouldPersistTaps="handled">
            {suggestions.map((prompt) => <Pressable key={prompt} onPress={() => sendMessage(prompt)} style={styles.prompt}><Text style={styles.promptText}>{prompt}</Text><Ionicons name="arrow-forward" size={12} color={palette.ink} /></Pressable>)}
          </ScrollView>}

          <View style={styles.composer}>
            <View style={styles.attach}><Ionicons name="sparkles-outline" size={17} color={palette.forest} /></View>
            <TextInput value={input} onChangeText={setInput} onSubmitEditing={() => sendMessage()} onFocus={() => requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }))} placeholder={activeTrip ? `Hỏi về ${activeTrip.destination}...` : 'Nhắn TravelMate AI...'} placeholderTextColor="#858A84" style={styles.composerInput} multiline maxLength={1000} textAlignVertical="center" />
            <Pressable disabled={!input.trim() || sending} onPress={() => sendMessage()} style={[styles.sendButton, (!input.trim() || sending) && styles.sendDisabled]}><Ionicons name="arrow-up" size={19} color={palette.white} /></Pressable>
          </View>
        </View>
        </View>
      </AppScreen>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardRoot: { flex: 1, backgroundColor: palette.cream },
  content: { paddingTop: 8, paddingBottom: 106, gap: 12 },
  contentKeyboard: { paddingTop: 6, paddingBottom: 8, gap: 7 },
  topbar: { minHeight: 42, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  online: { height: 32, paddingHorizontal: 11, flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(247,247,244,0.82)', borderRadius: radii.pill },
  onlineDot: { width: 7, height: 7, backgroundColor: palette.forestLight, borderRadius: 4 },
  onlineText: { color: palette.forest, fontSize: 9, fontWeight: '900' },
  checkingDot: { backgroundColor: palette.muted },
  offline: { backgroundColor: 'rgba(255,236,232,0.9)' },
  offlineDot: { backgroundColor: '#C44B3F' },
  offlineText: { color: '#8E3027' },
  heading: { paddingTop: 3 },
  eyebrow: { color: palette.forest, fontSize: 8, fontWeight: '900', letterSpacing: 1.4 },
  title: { marginTop: 7, color: palette.ink, fontSize: 31, lineHeight: 34, fontWeight: '900', letterSpacing: -1.4 },
  subtitle: { maxWidth: 330, marginTop: 6, color: palette.muted, fontSize: 10, lineHeight: 15 },
  tripDock: { height: 48, padding: 5, flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: 'rgba(247,247,244,0.92)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.78)', borderRadius: 17, ...shadows.card },
  tripDockIcon: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 12 },
  tripScroller: { height: 38, maxHeight: 38, flexGrow: 0, flexShrink: 1 },
  tripRail: { alignItems: 'center', gap: 6, paddingRight: 3 },
  tripChip: { height: 34, minWidth: 102, maxWidth: 148, paddingHorizontal: 11, flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#E8E9E5', borderRadius: 11 },
  tripChipActive: { backgroundColor: palette.ink },
  tripChipTitle: { maxWidth: 92, color: palette.ink, fontSize: 10, fontWeight: '900' },
  tripChipTitleActive: { color: palette.white },
  tripChipMeta: { color: palette.muted, fontSize: 8 },
  tripChipMetaActive: { color: 'rgba(255,255,255,0.58)' },
  chatShell: { flex: 1, minHeight: 0 },
  chatCard: { flex: 1, minHeight: 0, overflow: 'hidden', backgroundColor: '#D8DAD5', borderWidth: 1, borderColor: 'rgba(255,255,255,0.62)', borderRadius: 27, ...shadows.card },
  chatTop: { minHeight: 64, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 9, backgroundColor: palette.paper, borderBottomWidth: 1, borderBottomColor: palette.line },
  chatTopKeyboard: { minHeight: 54 },
  aiAvatar: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  chatIdentity: { flex: 1 },
  chatName: { color: palette.ink, fontSize: 12, fontWeight: '900' },
  chatContext: { marginTop: 2, color: palette.muted, fontSize: 8 },
  contextBadge: { height: 28, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#E3EFE5', borderRadius: 10 },
  contextBadgeText: { color: palette.forest, fontSize: 7, fontWeight: '900' },
  messageListFrame: { flex: 1, minHeight: 0 },
  messageList: { padding: 13, gap: 13 },
  messageRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 7 },
  messageRowUser: { justifyContent: 'flex-end' },
  miniAvatar: { width: 27, height: 27, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 10 },
  bubble: { maxWidth: '82%', paddingHorizontal: 13, paddingVertical: 10, borderRadius: 17 },
  assistantBubble: { backgroundColor: palette.paper, borderBottomLeftRadius: 5 },
  userBubble: { backgroundColor: palette.lime, borderBottomRightRadius: 5 },
  bubbleText: { color: palette.ink, fontSize: 11, lineHeight: 17 },
  typing: { marginTop: 7, flexDirection: 'row', alignItems: 'center', gap: 6 },
  typingText: { color: palette.forest, fontSize: 7, fontWeight: '800' },
  promptScroller: { height: 36, maxHeight: 36, flexGrow: 0 },
  promptRail: { paddingHorizontal: 10, gap: 6, alignItems: 'center' },
  prompt: { height: 30, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(247,247,244,0.78)', borderWidth: 1, borderColor: 'rgba(16,19,15,0.08)', borderRadius: radii.pill },
  promptText: { color: palette.ink, fontSize: 8, fontWeight: '800' },
  composer: { minHeight: 58, margin: 9, marginTop: 5, padding: 6, paddingLeft: 8, flexDirection: 'row', alignItems: 'flex-end', gap: 7, backgroundColor: palette.paper, borderWidth: 1, borderColor: 'rgba(255,255,255,0.85)', borderRadius: 19 },
  attach: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center', backgroundColor: '#E6ECE4', borderRadius: 12 },
  composerInput: { flex: 1, maxHeight: 84, paddingVertical: 10, color: palette.ink, fontSize: 11, lineHeight: 16 },
  sendButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 13 },
  sendDisabled: { opacity: 0.32 },
});
