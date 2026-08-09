import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, ImageBackground, LayoutAnimation, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Chip, EmptyState, GlassCard, LoadingState, PrimaryButton } from '@/components/ui';
import { TripShareSheet } from '@/components/trip/TripShareSheet';
import { palette, radii, shadows } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { useTravel } from '@/context/TravelContext';
import { useDestinationImage } from '@/hooks/useTravelImage';
import { Activity, apiRequest, Expense, ExpenseSummary, formatCompactMoney, formatDate, formatMoney, Itinerary, Trip } from '@/lib/api';

const categoryLabels: Record<string, string> = {
  FOOD: 'Ăn uống',
  TRANSPORT: 'Di chuyển',
  ACCOMMODATION: 'Lưu trú',
  ENTERTAINMENT: 'Vui chơi',
  SHOPPING: 'Mua sắm',
  OTHER: 'Khác',
};

const categoryIcons: Record<string, keyof typeof Ionicons.glyphMap> = {
  FOOD: 'restaurant-outline',
  TRANSPORT: 'car-outline',
  ACCOMMODATION: 'bed-outline',
  ENTERTAINMENT: 'ticket-outline',
  SHOPPING: 'bag-outline',
  OTHER: 'wallet-outline',
};

export default function TripDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const tripId = Number(id);
  const { trips, reloadTrips, setActiveTripId } = useTravel();
  const trip = trips.find((item) => item.id === tripId) ?? null;
  const tripImage = useDestinationImage(trip?.destination, trip?.coverImageUrl);
  const [tab, setTab] = useState<'itinerary' | 'expenses'>('itinerary');
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showExpense, setShowExpense] = useState(false);
  const [showShare, setShowShare] = useState(false);

  const load = useCallback(async () => {
    if (!tripId) return;
    setLoading(true);
    const [itineraryResult, expensesResult, summaryResult] = await Promise.allSettled([
      apiRequest<Itinerary>(`/api/v1/trips/${tripId}/itinerary`),
      apiRequest<Expense[]>(`/api/v1/trips/${tripId}/expenses`),
      apiRequest<ExpenseSummary>(`/api/v1/trips/${tripId}/expenses/summary`),
    ]);
    if (itineraryResult.status === 'fulfilled') setItinerary(itineraryResult.value);
    if (expensesResult.status === 'fulfilled') setExpenses(expensesResult.value);
    if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
    setLoading(false);
  }, [tripId]);

  useEffect(() => {
    setActiveTripId(tripId);
    load().catch(() => setLoading(false));
  }, [load, setActiveTripId, tripId]);

  async function generateItinerary() {
    if (!trip) return;
    setGenerating(true);
    try {
      await apiRequest('/api/v1/ai/generate-itinerary', { method: 'POST', body: JSON.stringify({ tripId: trip.id, travelStyle: trip.travelStyle, interests: ['ẩm thực', 'văn hoá'], specialRequests: 'Lộ trình cân bằng, có thời gian nghỉ và tối ưu di chuyển' }) });
      await load();
    } catch (cause) {
      Alert.alert('Chưa thể tạo lịch trình', cause instanceof Error ? cause.message : 'Vui lòng thử lại.');
    } finally {
      setGenerating(false);
    }
  }

  async function toggleActivity(dayId: number, activity: Activity) {
    await apiRequest(`/api/v1/trips/${tripId}/itinerary/days/${dayId}/activities/${activity.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: activity.status === 'DONE' ? 'PLANNED' : 'DONE' }) });
    await load();
  }

  if (!trip) return <View style={styles.fallback}><SafeAreaView><LoadingState label="Đang mở hành trình..." /><PrimaryButton label="Quay lại" variant="ghost" onPress={() => router.back()} /></SafeAreaView></View>;

  return (
    <View style={styles.screen}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <ImageBackground source={tripImage.source} style={styles.hero} imageStyle={styles.heroImage}>
          <LinearGradient colors={['rgba(4,24,19,0.13)', 'rgba(4,24,19,0.88)']} style={[StyleSheet.absoluteFill, styles.heroImage]} />
          <SafeAreaView style={styles.heroSafe} edges={['top']}>
            <View style={styles.heroTop}><Pressable onPress={() => router.back()} style={styles.iconButton}><Ionicons name="arrow-back" size={20} color={palette.white} /></Pressable><View style={styles.heroActions}><Pressable onPress={() => setShowShare(true)} style={styles.iconButton} accessibilityRole="button" accessibilityLabel="Chia sẻ chuyến đi"><Ionicons name="share-outline" size={19} color={palette.white} /></Pressable><Pressable onPress={reloadTrips} style={styles.iconButton}><Ionicons name="refresh" size={19} color={palette.white} /></Pressable></View></View>
            <View style={styles.heroCopy}><Chip label={trip.status} icon="radio-button-on" active /><Text style={styles.destination}>{trip.destination}</Text><Text style={styles.tripName}>{trip.name}</Text><View style={styles.heroMeta}><Text style={styles.heroMetaText}><Ionicons name="calendar-outline" size={13} /> {trip.durationDays} ngày</Text><Text style={styles.heroMetaText}><Ionicons name="people-outline" size={13} /> {trip.numPeople} người</Text><Text style={styles.heroMetaText}><Ionicons name="wallet-outline" size={13} /> {formatCompactMoney(trip.budget)}</Text></View></View>
          </SafeAreaView>
        </ImageBackground>

        <View style={styles.body}>
          <View style={styles.tabs}><Pressable onPress={() => setTab('itinerary')} style={[styles.tab, tab === 'itinerary' && styles.tabActive]}><Ionicons name="calendar-outline" size={17} color={tab === 'itinerary' ? palette.ink : palette.muted} /><Text style={[styles.tabText, tab === 'itinerary' && styles.tabTextActive]}>Lịch trình</Text></Pressable><Pressable onPress={() => setTab('expenses')} style={[styles.tab, tab === 'expenses' && styles.tabActive]}><Ionicons name="wallet-outline" size={17} color={tab === 'expenses' ? palette.ink : palette.muted} /><Text style={[styles.tabText, tab === 'expenses' && styles.tabTextActive]}>Chi tiêu</Text></Pressable></View>
          {loading ? <LoadingState /> : tab === 'itinerary' ? <ItineraryTab itinerary={itinerary} onGenerate={generateItinerary} generating={generating} onToggle={toggleActivity} /> : <ExpensesTab trip={trip} expenses={expenses} summary={summary} onAdd={() => setShowExpense(true)} />}
        </View>
      </ScrollView>
      <AddExpenseModal visible={showExpense} trip={trip} onClose={() => setShowExpense(false)} onSaved={async () => { setShowExpense(false); await load(); }} />
      <TripShareSheet visible={showShare} trip={trip} onClose={() => setShowShare(false)} />
    </View>
  );
}

function ItineraryTab({ itinerary, onGenerate, generating, onToggle }: { itinerary: Itinerary | null; onGenerate: () => void; generating: boolean; onToggle: (dayId: number, activity: Activity) => Promise<void> }) {
  const [expandedActivityId, setExpandedActivityId] = useState<number | null>(null);
  const [togglingActivityId, setTogglingActivityId] = useState<number | null>(null);

  if (!itinerary?.days?.length) return <EmptyState icon="calendar-outline" title="Lịch trình chưa được tạo" message="TravelMate AI có thể dựng lịch theo số ngày, sở thích và ngân sách của chuyến đi." action={<PrimaryButton label="Để AI tạo lịch trình" icon="sparkles" loading={generating} onPress={onGenerate} />} />;

  function toggleDetails(activityId: number) {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedActivityId((current) => current === activityId ? null : activityId);
  }

  async function completeActivity(dayId: number, activity: Activity) {
    if (togglingActivityId !== null) return;
    setTogglingActivityId(activity.id);
    try {
      await onToggle(dayId, activity);
    } finally {
      setTogglingActivityId(null);
    }
  }

  return (
    <View style={styles.dayList}>
      {itinerary.days.map((day) => (
        <GlassCard key={day.id} style={styles.dayCard}>
          <View style={styles.dayHeader}>
            <View style={styles.dayNumber}><Text style={styles.dayNumberText}>{String(day.dayNumber).padStart(2, '0')}</Text></View>
            <View style={styles.dayCopy}><Text style={styles.dayLabel}>NGÀY {day.dayNumber}</Text><Text style={styles.dayDate}>{formatDate(day.date)}</Text></View>
            <View style={styles.daySummary}><Text style={styles.dayCost}>{formatCompactMoney(day.totalEstimatedCost)}</Text><Text style={styles.dayActivityCount}>{day.activities.length} hoạt động</Text></View>
          </View>
          {day.note ? <Text style={styles.dayNote}>{day.note}</Text> : null}
          <View style={styles.timeline}>
            {day.activities.map((activity, index) => {
              const done = activity.status === 'DONE';
              const expanded = expandedActivityId === activity.id;
              const toggling = togglingActivityId === activity.id;
              return (
                <Pressable key={activity.id} onPress={() => toggleDetails(activity.id)} style={[styles.activity, expanded && styles.activityExpanded]} accessibilityRole="button" accessibilityHint="Mở chi tiết hoạt động">
                  <View style={styles.activityRail}>
                    <Pressable
                      onPress={(event) => { event.stopPropagation(); completeActivity(day.id, activity).catch(() => undefined); }}
                      disabled={toggling}
                      hitSlop={9}
                      style={[styles.activityDot, done && styles.activityDone]}
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: done, busy: toggling }}
                      accessibilityLabel={done ? 'Đánh dấu chưa hoàn thành' : 'Đánh dấu hoàn thành'}
                    >
                      {toggling ? <ActivityIndicator size="small" color={palette.ink} /> : done ? <Ionicons name="checkmark" size={13} color={palette.ink} /> : <View style={styles.activityDotInner} />}
                    </Pressable>
                    {index < day.activities.length - 1 && <View style={styles.activityLine} />}
                  </View>
                  <View style={styles.activityTime}>
                    <Text style={styles.activityTimeText}>{activity.startTime?.slice(0, 5) ?? '--:--'}</Text>
                    <Text style={styles.activityEndTime}>{activity.endTime?.slice(0, 5) ?? 'linh hoạt'}</Text>
                  </View>
                  <View style={styles.activityCopy}>
                    <View style={styles.activityTitleRow}>
                      <View style={styles.activityTitleCopy}>
                        <Text style={[styles.activityName, done && styles.activityNameDone]}>{activity.name}</Text>
                        <Text style={styles.activityPlace}>{activity.place?.name ?? activity.type}</Text>
                      </View>
                      <View style={[styles.statusPill, done && styles.statusPillDone]}><Text style={styles.statusPillText}>{done ? 'XONG' : 'SẮP TỚI'}</Text></View>
                      <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={15} color={palette.muted} />
                    </View>
                    <View style={styles.activityMeta}>
                      <Text style={styles.activityMetaText} numberOfLines={1}><Ionicons name="location-outline" size={11} /> {activity.place?.address ?? 'Theo lịch trình'}</Text>
                      {activity.estimatedCost ? <Text style={styles.activityCost}>{formatCompactMoney(activity.estimatedCost)}</Text> : <Text style={styles.activityCost}>Miễn phí/chưa rõ</Text>}
                    </View>
                    {expanded && <View style={styles.activityDetails}>
                      <Text style={styles.activityDetailsTitle}>CHI TIẾT ĐIỂM DỪNG</Text>
                      <Text style={styles.activityDescription}>{activity.description || activity.note || 'Chưa có ghi chú bổ sung. Bạn có thể dùng TravelMate AI để hỏi thêm về điểm dừng này.'}</Text>
                      <View style={styles.activityFacts}>
                        <View style={styles.activityFact}><Ionicons name="time-outline" size={14} color={palette.forest} /><Text style={styles.activityFactText}>{activity.startTime?.slice(0, 5) ?? '--:--'} – {activity.endTime?.slice(0, 5) ?? 'linh hoạt'}</Text></View>
                        {activity.place?.rating ? <View style={styles.activityFact}><Ionicons name="star" size={13} color={palette.lime} /><Text style={styles.activityFactText}>{activity.place.rating}/5</Text></View> : null}
                      </View>
                      <Text style={styles.activityCompleteHint}>{done ? 'Chạm ô vàng để đưa hoạt động về trạng thái dự kiến.' : 'Chạm vòng tròn bên trái khi bạn đã hoàn thành.'}</Text>
                    </View>}
                  </View>
                </Pressable>
              );
            })}
          </View>
        </GlassCard>
      ))}
    </View>
  );
}

function ExpensesTab({ trip, expenses, summary, onAdd }: { trip: Trip; expenses: Expense[]; summary: ExpenseSummary | null; onAdd: () => void }) {
  const spent = summary?.totalExpense ?? expenses.reduce((sum, expense) => sum + Number(expense.amount), 0);
  const budget = summary?.budget ?? trip.budget;
  const progress = Math.min(100, budget ? (spent / budget) * 100 : 0);
  return <View style={styles.expenseSection}><GlassCard dark style={styles.budgetCard}><Text style={styles.budgetEyebrow}>TỔNG QUAN NGÂN SÁCH</Text><Text style={styles.budgetValue}>{formatMoney(spent)}</Text><Text style={styles.budgetCaption}>đã dùng trên {formatMoney(budget)}</Text><View style={styles.progressTrack}><View style={[styles.progressBar, { width: `${progress}%` }]} /></View><View style={styles.budgetFooter}><Text style={styles.budgetFooterText}>Còn lại</Text><Text style={styles.budgetFooterText}>{formatMoney(Math.max(0, budget - spent))}</Text></View></GlassCard><View style={styles.expenseHeader}><View><Text style={styles.expenseEyebrow}>NHẬT KÝ CHI TIÊU</Text><Text style={styles.expenseTitle}>{expenses.length} khoản đã ghi</Text></View><Pressable onPress={onAdd} style={styles.addExpense}><Ionicons name="add" size={20} color={palette.ink} /></Pressable></View>{expenses.length === 0 ? <EmptyState icon="receipt-outline" title="Chưa có khoản chi" message="Ghi khoản đầu tiên để biết chuyến đi đang bám ngân sách tới đâu." action={<PrimaryButton label="Thêm khoản chi" onPress={onAdd} />} /> : <GlassCard style={styles.expenseList}>{expenses.map((expense, index) => <View key={expense.id}><View style={styles.expenseRow}><View style={styles.expenseIcon}><Ionicons name={categoryIcons[expense.category] ?? 'wallet-outline'} size={17} color={palette.forestLight} /></View><View style={styles.expenseCopy}><Text style={styles.expenseName}>{expense.name}</Text><Text style={styles.expenseMeta}>{categoryLabels[expense.category] ?? expense.category} • {formatDate(expense.expenseDate)}</Text></View><Text style={styles.expenseAmount}>{formatCompactMoney(expense.amount)}</Text></View>{index < expenses.length - 1 && <View style={styles.expenseDivider} />}</View>)}</GlassCard>}</View>;
}

function AddExpenseModal({ visible, trip, onClose, onSaved }: { visible: boolean; trip: Trip; onClose: () => void; onSaved: () => Promise<void> }) {
  const { user } = useSession();
  const [form, setForm] = useState({ name: '', amount: '', category: 'FOOD', expenseDate: new Date().toISOString().slice(0, 10), note: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function save() {
    if (!form.name.trim() || Number(form.amount) <= 0 || !user) { setError('Nhập tên và số tiền hợp lệ.'); return; }
    setLoading(true); setError('');
    try {
      await apiRequest(`/api/v1/trips/${trip.id}/expenses`, { method: 'POST', body: JSON.stringify({ ...form, amount: Number(form.amount), paidByUserId: user.id, splitType: 'SINGLE' }) });
      await onSaved();
      setForm({ name: '', amount: '', category: 'FOOD', expenseDate: new Date().toISOString().slice(0, 10), note: '' });
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa thể lưu khoản chi.'); }
    finally { setLoading(false); }
  }
  return <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}><View style={styles.modalBackdrop}><SafeAreaView style={styles.expenseModal} edges={['bottom']}><View style={styles.modalHandle} /><View style={styles.modalHeader}><View><Text style={styles.modalEyebrow}>KHOẢN CHI MỚI</Text><Text style={styles.modalTitle}>Ghi lại chi tiêu</Text></View><Pressable onPress={onClose} style={styles.modalClose}><Ionicons name="close" size={20} /></Pressable></View><View style={styles.expenseForm}><Input label="Nội dung" value={form.name} onChangeText={(name) => setForm({ ...form, name })} placeholder="Bữa tối bên sông" /><Input label="Số tiền" value={form.amount} onChangeText={(amount) => setForm({ ...form, amount })} keyboardType="numeric" placeholder="500000" /><View><Text style={styles.inputLabel}>Danh mục</Text><View style={styles.categoryChips}>{Object.entries(categoryLabels).map(([value, label]) => <Chip key={value} label={label} active={form.category === value} onPress={() => setForm({ ...form, category: value })} />)}</View></View><Input label="Ngày chi" value={form.expenseDate} onChangeText={(expenseDate) => setForm({ ...form, expenseDate })} placeholder="YYYY-MM-DD" />{error ? <Text style={styles.modalError}>{error}</Text> : null}<PrimaryButton label="Lưu khoản chi" icon="checkmark" loading={loading} onPress={save} /></View></SafeAreaView></View></Modal>;
}

function Input({ label, ...props }: React.ComponentProps<typeof TextInput> & { label: string }) {
  return <View><Text style={styles.inputLabel}>{label}</Text><TextInput style={styles.input} placeholderTextColor="#91A09A" {...props} /></View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.cream },
  content: { paddingBottom: 52 },
  fallback: { flex: 1, padding: 22, backgroundColor: palette.cream },
  hero: { height: 390 },
  heroImage: { borderBottomLeftRadius: 31, borderBottomRightRadius: 31 },
  heroSafe: { flex: 1, padding: 17 },
  heroTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  heroActions: { flexDirection: 'row', gap: 8 },
  iconButton: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(5,30,24,0.48)', borderWidth: 1, borderColor: palette.whiteLine, borderRadius: 15 },
  heroCopy: { marginTop: 'auto', gap: 7 },
  destination: { color: palette.lime, fontSize: 8, fontWeight: '900', letterSpacing: 1.2 },
  tripName: { color: palette.white, fontSize: 34, lineHeight: 37, fontWeight: '900', letterSpacing: -1.5 },
  heroMeta: { marginTop: 4, flexDirection: 'row', flexWrap: 'wrap', gap: 13 },
  heroMetaText: { color: 'rgba(255,255,255,0.68)', fontSize: 9 },
  body: { padding: 17, gap: 17 },
  tabs: { padding: 5, flexDirection: 'row', backgroundColor: 'rgba(255,255,252,0.72)', borderRadius: 18, ...shadows.card },
  tab: { flex: 1, minHeight: 45, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14 },
  tabActive: { backgroundColor: palette.lime },
  tabText: { color: palette.muted, fontSize: 9, fontWeight: '800' },
  tabTextActive: { color: palette.ink },
  dayList: { gap: 13 },
  dayCard: { padding: 16 },
  dayHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  dayNumber: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  dayNumberText: { color: palette.ink, fontSize: 12, fontWeight: '900' },
  dayCopy: { flex: 1 },
  dayLabel: { color: '#73901F', fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  dayDate: { marginTop: 4, color: palette.ink, fontSize: 13, fontWeight: '900' },
  daySummary: { alignItems: 'flex-end', gap: 3 },
  dayCost: { color: palette.muted, fontSize: 8, fontWeight: '800' },
  dayActivityCount: { color: palette.forest, fontSize: 7, fontWeight: '800' },
  dayNote: { marginTop: 12, padding: 10, color: palette.muted, backgroundColor: '#F3F6EF', borderRadius: 12, fontSize: 8, lineHeight: 13 },
  timeline: { marginTop: 15 },
  activity: { minHeight: 88, flexDirection: 'row', borderRadius: 16 },
  activityExpanded: { marginHorizontal: -7, paddingHorizontal: 7, paddingTop: 7, backgroundColor: '#F1F2EE' },
  activityRail: { width: 31, alignItems: 'center' },
  activityDot: { width: 25, height: 25, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderWidth: 2, borderColor: '#B8C5BC', borderRadius: 13 },
  activityDone: { backgroundColor: palette.lime, borderColor: palette.lime },
  activityDotInner: { width: 7, height: 7, backgroundColor: '#D5DDD6', borderRadius: 4 },
  activityLine: { width: 1, flex: 1, backgroundColor: '#DDE5DE' },
  activityTime: { width: 49, paddingTop: 4 },
  activityTimeText: { color: '#6E8429', fontSize: 9, fontWeight: '900' },
  activityEndTime: { marginTop: 3, color: palette.muted, fontSize: 6 },
  activityCopy: { flex: 1, minWidth: 0, paddingBottom: 17 },
  activityTitleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 6 },
  activityTitleCopy: { flex: 1, minWidth: 0 },
  activityName: { color: palette.ink, fontSize: 11, fontWeight: '900' },
  activityNameDone: { color: '#91A09A', textDecorationLine: 'line-through' },
  activityPlace: { marginTop: 4, color: palette.muted, fontSize: 8 },
  statusPill: { marginTop: -2, paddingHorizontal: 6, paddingVertical: 4, backgroundColor: '#E5E7E2', borderRadius: radii.pill },
  statusPillDone: { backgroundColor: palette.limeSoft },
  statusPillText: { color: palette.ink, fontSize: 5, fontWeight: '900', letterSpacing: 0.4 },
  activityMeta: { marginTop: 7, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 5 },
  activityMetaText: { flex: 1, color: '#87958F', fontSize: 7 },
  activityCost: { color: palette.forest, fontSize: 7, fontWeight: '900' },
  activityDetails: { marginTop: 11, paddingTop: 11, borderTopWidth: 1, borderTopColor: palette.line },
  activityDetailsTitle: { color: palette.forest, fontSize: 6, fontWeight: '900', letterSpacing: 0.9 },
  activityDescription: { marginTop: 6, color: palette.inkSoft, fontSize: 8, lineHeight: 13 },
  activityFacts: { marginTop: 9, flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  activityFact: { paddingHorizontal: 8, paddingVertical: 6, flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: palette.white, borderRadius: 9 },
  activityFactText: { color: palette.ink, fontSize: 7, fontWeight: '800' },
  activityCompleteHint: { marginTop: 9, color: palette.muted, fontSize: 7, lineHeight: 11, fontStyle: 'italic' },
  expenseSection: { gap: 14 },
  budgetCard: { overflow: 'hidden' },
  budgetEyebrow: { color: palette.lime, fontSize: 7, fontWeight: '900', letterSpacing: 1.1 },
  budgetValue: { marginTop: 11, color: palette.white, fontSize: 30, fontWeight: '900', letterSpacing: -1.2 },
  budgetCaption: { marginTop: 3, color: 'rgba(255,255,255,0.48)', fontSize: 8 },
  progressTrack: { height: 7, marginTop: 18, overflow: 'hidden', backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 4 },
  progressBar: { height: '100%', backgroundColor: palette.lime, borderRadius: 4 },
  budgetFooter: { marginTop: 10, flexDirection: 'row', justifyContent: 'space-between' },
  budgetFooterText: { color: 'rgba(255,255,255,0.56)', fontSize: 8 },
  expenseHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  expenseEyebrow: { color: '#78931E', fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  expenseTitle: { marginTop: 4, color: palette.ink, fontSize: 18, fontWeight: '900' },
  addExpense: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  expenseList: { paddingVertical: 7 },
  expenseRow: { minHeight: 68, flexDirection: 'row', alignItems: 'center', gap: 11 },
  expenseIcon: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.sage, borderRadius: 14 },
  expenseCopy: { flex: 1 },
  expenseName: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  expenseMeta: { marginTop: 4, color: palette.muted, fontSize: 7 },
  expenseAmount: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  expenseDivider: { height: 1, marginLeft: 51, backgroundColor: palette.line },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(4,25,20,0.58)' },
  expenseModal: { padding: 20, backgroundColor: palette.cream, borderTopLeftRadius: 30, borderTopRightRadius: 30 },
  modalHandle: { width: 42, height: 4, alignSelf: 'center', marginBottom: 18, backgroundColor: '#CBD5CC', borderRadius: 2 },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  modalEyebrow: { color: '#75921F', fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  modalTitle: { marginTop: 4, color: palette.ink, fontSize: 25, fontWeight: '900' },
  modalClose: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderRadius: 14 },
  expenseForm: { marginTop: 20, gap: 13 },
  inputLabel: { marginBottom: 7, color: palette.inkSoft, fontSize: 8, fontWeight: '900' },
  input: { minHeight: 50, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  categoryChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  modalError: { padding: 10, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: radii.sm, fontSize: 8 },
});
