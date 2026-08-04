import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { generateItinerary } from '@/features/ai/itinerary-service';
import type {
  BudgetBreakdown,
  ItineraryActivity,
  ItineraryPlan,
  ItineraryRequest,
} from '@/features/ai/itinerary-types';

const periodLabels: Record<ItineraryActivity['period'], string> = {
  morning: 'Buổi sáng',
  afternoon: 'Buổi chiều',
  evening: 'Buổi tối',
};

function parsePositiveNumber(value: string): number | undefined {
  const parsed = Number(value.replace(/\D/g, ''));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

function formatMoney(value: number): string {
  return `${new Intl.NumberFormat('vi-VN').format(value)} VND`;
}

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data.detail ?? 'AI Service chưa thể tạo lịch trình.';
  }
  return 'Không kết nối được AI Service. Hãy kiểm tra FastAPI và thử lại.';
}

function BudgetPreview({ budget }: { budget: BudgetBreakdown }) {
  const rows = [
    ['Lưu trú', budget.accommodationVnd],
    ['Ăn uống', budget.foodVnd],
    ['Di chuyển', budget.transportVnd],
    ['Trải nghiệm', budget.activitiesVnd],
    ['Dự phòng', budget.reserveVnd],
  ] as const;

  return (
    <View style={styles.budgetCard}>
      <View style={styles.sectionHeadingRow}>
        <Text style={styles.sectionTitle}>Phân bổ ngân sách</Text>
        <Text style={styles.budgetTotal}>{formatMoney(budget.totalVnd)}</Text>
      </View>
      {rows.map(([label, value]) => (
        <View key={label} style={styles.budgetRow}>
          <Text style={styles.budgetLabel}>{label}</Text>
          <Text style={styles.budgetValue}>{formatMoney(value)}</Text>
        </View>
      ))}
      <Text style={styles.helperText}>
        Các khoản do hệ thống tính để tổng luôn khớp ngân sách. Giá thực tế cần được kiểm tra.
      </Text>
    </View>
  );
}

function PlanPreview({ plan }: { plan: ItineraryPlan }) {
  return (
    <View style={styles.previewArea}>
      <View style={styles.summaryCard}>
        <Text style={styles.previewEyebrow}>BẢN NHÁP AI</Text>
        <Text style={styles.previewTitle}>
          {plan.destination} · {plan.durationDays} ngày
        </Text>
        <Text style={styles.summaryText}>{plan.summary}</Text>
        {plan.assumptions.map((assumption) => (
          <Text key={assumption} style={styles.assumptionText}>
            • {assumption}
          </Text>
        ))}
      </View>

      <BudgetPreview budget={plan.budget} />

      {plan.days.map((day) => (
        <View key={day.day} style={styles.dayCard}>
          <View style={styles.dayNumber}>
            <Text style={styles.dayNumberText}>{day.day}</Text>
          </View>
          <View style={styles.dayContent}>
            <Text style={styles.dayTitle}>{day.title}</Text>
            {day.activities.map((activity, index) => (
              <View key={`${day.day}-${activity.period}-${index}`} style={styles.activityRow}>
                <View style={styles.activityDot} />
                <View style={styles.activityContent}>
                  <Text style={styles.periodText}>{periodLabels[activity.period]}</Text>
                  <Text style={styles.activityTitle}>{activity.title}</Text>
                  {activity.placeName ? (
                    <Text style={styles.activityMeta}>{activity.placeName}</Text>
                  ) : null}
                  {activity.notes ? <Text style={styles.activityNotes}>{activity.notes}</Text> : null}
                </View>
              </View>
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}

export default function TripsScreen() {
  const [destination, setDestination] = useState('');
  const [durationDays, setDurationDays] = useState('');
  const [numPeople, setNumPeople] = useState('');
  const [budget, setBudget] = useState('');
  const [preferences, setPreferences] = useState('');
  const [notes, setNotes] = useState('');
  const [accepted, setAccepted] = useState(false);

  const mutation = useMutation({
    mutationFn: generateItinerary,
    onSuccess: () => setAccepted(false),
  });

  const plan = mutation.data?.plan ?? null;
  const providerLabel = useMemo(() => {
    if (mutation.data?.provider === 'local') return 'Qwen local';
    if (mutation.data?.provider === 'gemini') return 'Gemini API';
    if (mutation.data?.provider === 'mock') return 'Mock API';
    return null;
  }, [mutation.data?.provider]);

  function submit() {
    if (mutation.isPending) return;
    const request: ItineraryRequest = {
      destination: destination.trim() || undefined,
      durationDays: parsePositiveNumber(durationDays),
      numPeople: parsePositiveNumber(numPeople),
      budgetVnd: parsePositiveNumber(budget),
      preferences: preferences
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      notes: notes.trim() || undefined,
    };
    mutation.mutate(request);
  }

  return (
    <SafeAreaView edges={['bottom']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
        style={styles.container}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <View>
              <Text style={styles.eyebrow}>TRAVELMATE PLANNER</Text>
              <Text style={styles.title}>Tạo lịch trình AI</Text>
            </View>
            {providerLabel ? (
              <View style={styles.providerBadge}>
                <View style={styles.statusDot} />
                <Text style={styles.providerText}>{providerLabel}</Text>
              </View>
            ) : null}
          </View>

          <View style={styles.formCard}>
            <Text style={styles.formIntro}>
              Điền những gì bạn đã biết. TravelMate sẽ hỏi lại nếu thiếu thông tin quan trọng.
            </Text>

            <Text style={styles.fieldLabel}>Điểm đến</Text>
            <TextInput
              value={destination}
              onChangeText={setDestination}
              placeholder="Ví dụ: Đà Nẵng"
              style={styles.input}
            />

            <View style={styles.formRow}>
              <View style={styles.flexField}>
                <Text style={styles.fieldLabel}>Số ngày</Text>
                <TextInput
                  value={durationDays}
                  onChangeText={setDurationDays}
                  keyboardType="number-pad"
                  placeholder="3"
                  style={styles.input}
                />
              </View>
              <View style={styles.flexField}>
                <Text style={styles.fieldLabel}>Số người</Text>
                <TextInput
                  value={numPeople}
                  onChangeText={setNumPeople}
                  keyboardType="number-pad"
                  placeholder="2"
                  style={styles.input}
                />
              </View>
            </View>

            <Text style={styles.fieldLabel}>Tổng ngân sách (VND)</Text>
            <TextInput
              value={budget}
              onChangeText={setBudget}
              keyboardType="number-pad"
              placeholder="5000000"
              style={styles.input}
            />

            <Text style={styles.fieldLabel}>Sở thích, ngăn cách bằng dấu phẩy</Text>
            <TextInput
              value={preferences}
              onChangeText={setPreferences}
              placeholder="biển, ẩm thực, nghỉ dưỡng"
              style={styles.input}
            />

            <Text style={styles.fieldLabel}>Lưu ý thêm</Text>
            <TextInput
              value={notes}
              onChangeText={setNotes}
              multiline
              placeholder="Có trẻ nhỏ, hạn chế di chuyển xa..."
              style={[styles.input, styles.notesInput]}
            />

            <Pressable
              accessibilityRole="button"
              disabled={mutation.isPending}
              onPress={submit}
              style={({ pressed }) => [
                styles.generateButton,
                mutation.isPending && styles.generateButtonDisabled,
                pressed && styles.buttonPressed,
              ]}>
              {mutation.isPending ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.generateButtonText}>Tạo lịch trình</Text>
              )}
            </Pressable>
          </View>

          {mutation.data?.status === 'needs_clarification' ? (
            <View style={styles.questionCard}>
              <Text style={styles.questionTitle}>Cần thêm thông tin</Text>
              {mutation.data.questions.map((question) => (
                <Text key={question} style={styles.questionText}>
                  • {question}
                </Text>
              ))}
            </View>
          ) : null}

          {mutation.error ? (
            <View style={styles.errorCard}>
              <Text style={styles.errorText}>{getErrorMessage(mutation.error)}</Text>
            </View>
          ) : null}

          {plan ? (
            <>
              <PlanPreview plan={plan} />
              <Pressable
                accessibilityRole="button"
                onPress={() => setAccepted(true)}
                style={({ pressed }) => [styles.acceptButton, pressed && styles.buttonPressed]}>
                <Text style={styles.acceptButtonText}>Dùng lịch trình này</Text>
              </Pressable>
              {accepted ? (
                <View style={styles.acceptedCard}>
                  <Text style={styles.acceptedTitle}>Đã chọn bản nháp</Text>
                  <Text style={styles.acceptedText}>
                    Lịch trình đã được giữ trong phiên hiện tại. Bước lưu lâu dài sẽ nối với Core
                    API khi module chuyến đi được triển khai.
                  </Text>
                </View>
              ) : null}
            </>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F4FAF7' },
  container: { flex: 1 },
  scrollContent: {
    width: '100%',
    maxWidth: 920,
    alignSelf: 'center',
    gap: 14,
    padding: 18,
    paddingBottom: 36,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  eyebrow: { color: '#16775A', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  title: { marginTop: 2, color: '#17352D', fontSize: 25, fontWeight: '800' },
  providerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#E7F2EE',
  },
  statusDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#21A179' },
  providerText: { color: '#48645C', fontSize: 11, fontWeight: '700' },
  formCard: {
    gap: 7,
    padding: 16,
    borderWidth: 1,
    borderColor: '#DDEAE5',
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  formIntro: { marginBottom: 6, color: '#587168', fontSize: 13, lineHeight: 19 },
  fieldLabel: { marginTop: 3, color: '#526A62', fontSize: 11, fontWeight: '700' },
  input: {
    minHeight: 42,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#D8E5E0',
    borderRadius: 12,
    backgroundColor: '#F8FAF9',
    color: '#17352D',
    fontSize: 14,
  },
  notesInput: { minHeight: 72, textAlignVertical: 'top' },
  formRow: { flexDirection: 'row', gap: 10 },
  flexField: { flex: 1, gap: 7 },
  generateButton: {
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    borderRadius: 14,
    backgroundColor: '#16775A',
  },
  generateButtonDisabled: { backgroundColor: '#8FB9AA' },
  generateButtonText: { color: '#FFFFFF', fontSize: 15, fontWeight: '800' },
  buttonPressed: { opacity: 0.82 },
  questionCard: { padding: 15, borderRadius: 16, backgroundColor: '#FFF8E8' },
  questionTitle: { marginBottom: 5, color: '#845E10', fontSize: 14, fontWeight: '800' },
  questionText: { color: '#6F5C32', fontSize: 13, lineHeight: 20 },
  errorCard: { padding: 14, borderRadius: 14, backgroundColor: '#FFF0EF' },
  errorText: { color: '#A23D35', fontSize: 13, lineHeight: 19 },
  previewArea: { gap: 12 },
  summaryCard: { padding: 16, borderRadius: 18, backgroundColor: '#173F34' },
  previewEyebrow: { color: '#8FDBC0', fontSize: 10, fontWeight: '800', letterSpacing: 1.1 },
  previewTitle: { marginTop: 4, color: '#FFFFFF', fontSize: 22, fontWeight: '800' },
  summaryText: { marginTop: 8, color: '#E3F1EC', fontSize: 14, lineHeight: 21 },
  assumptionText: { marginTop: 6, color: '#BFD8CF', fontSize: 12, lineHeight: 18 },
  budgetCard: {
    padding: 15,
    borderWidth: 1,
    borderColor: '#DDEAE5',
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  sectionHeadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sectionTitle: { color: '#29483F', fontSize: 15, fontWeight: '800' },
  budgetTotal: { color: '#16775A', fontSize: 13, fontWeight: '800' },
  budgetRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 5,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5EEEA',
  },
  budgetLabel: { color: '#61766F', fontSize: 13 },
  budgetValue: { color: '#29483F', fontSize: 13, fontWeight: '700' },
  helperText: { marginTop: 9, color: '#7A8E87', fontSize: 11, lineHeight: 16 },
  dayCard: {
    flexDirection: 'row',
    gap: 12,
    padding: 15,
    borderWidth: 1,
    borderColor: '#DDEAE5',
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  dayNumber: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    backgroundColor: '#D9F1E8',
  },
  dayNumberText: { color: '#16775A', fontSize: 13, fontWeight: '800' },
  dayContent: { flex: 1, gap: 9 },
  dayTitle: { color: '#29483F', fontSize: 16, fontWeight: '800' },
  activityRow: { flexDirection: 'row', gap: 9 },
  activityDot: {
    width: 7,
    height: 7,
    marginTop: 7,
    borderRadius: 4,
    backgroundColor: '#67B69A',
  },
  activityContent: { flex: 1 },
  periodText: { color: '#16775A', fontSize: 10, fontWeight: '800', textTransform: 'uppercase' },
  activityTitle: { marginTop: 1, color: '#29483F', fontSize: 14, fontWeight: '700' },
  activityMeta: { marginTop: 2, color: '#61766F', fontSize: 12 },
  activityNotes: { marginTop: 3, color: '#7A8E87', fontSize: 11, lineHeight: 16 },
  acceptButton: {
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#16775A',
    borderRadius: 14,
    backgroundColor: '#FFFFFF',
  },
  acceptButtonText: { color: '#16775A', fontSize: 14, fontWeight: '800' },
  acceptedCard: { padding: 14, borderRadius: 14, backgroundColor: '#E7F5EF' },
  acceptedTitle: { color: '#16775A', fontSize: 14, fontWeight: '800' },
  acceptedText: { marginTop: 3, color: '#48645C', fontSize: 12, lineHeight: 18 },
});
