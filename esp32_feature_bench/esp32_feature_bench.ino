/*
  Белгілер векторын есептеу уақытын ESP32-S3 тақтасында өлшеу.

  Зерттеу жұмысының 3.1-тармағында сипатталған бес статистика есептеледі:
  орташа мән, стандартты ауытқу, размах, еңкею коэффициенті (slope) және
  орташа сызықты қиып өту жиілігі (ZCR). Он жеті арнада олар 85 элементті
  вектор береді.

  Датчиктер қажет емес: терезе синтетикалық сигналмен толтырылады.
  Мақсат - есептеудің өзіне кететін уақытты өлшеу және оны 2.6-тармақтағы
  20 мс бюджетімен салыстыру.

  Тақта: ESP32-S3 DevKitC-1
  Arduino IDE: Tools -> Board -> ESP32S3 Dev Module
  Егер монитор портында ештеңе шықпаса: Tools -> USB CDC On Boot -> Enabled
*/

#include <Arduino.h>
#include <math.h>

#define WIN     50                  // терезедегі есептеу саны (1 секунд, 50 Гц)
#define N_CH    17                  // 5 иілу + 6 алақан IMU + 6 білек IMU
#define N_STAT  5                   // бір арнаға статистика
#define N_FEAT  (N_CH * N_STAT)     // 17 x 5 = 85
#define REPEAT  500                 // уақытты өлшеу үшін қайталау саны

static float win[WIN][N_CH];
static float feat[N_FEAT];
volatile float sink = 0.0f;         // оптимизатор циклді алып тастамауы үшін

// t = 0..N-1 болғанда sum((t - tbar)^2) = N*(N*N-1)/12
static const float SLOPE_DEN = (float)WIN * ((float)WIN * WIN - 1.0f) / 12.0f;
static const float T_BAR     = ((float)WIN - 1.0f) / 2.0f;
static const float PI_F      = 3.14159265f;

// ------------------------------------------------- детерминді псевдокездейсоқ
static uint32_t rndState = 12345u;

static float nextRand() {
  rndState = rndState * 1664525u + 1013904223u;
  return (float)((rndState >> 8) & 0xFFFFu) / 65535.0f - 0.5f;
}

// ------------------------------------------------- терезені толтыру
static void fillWindow() {
  rndState = 12345u;
  for (int i = 0; i < WIN; i++) {
    // 0-арна: сызықтық өсу, статистикалары формуламен дәл белгілі
    win[i][0] = 0.02f * (float)i + 0.1f;
    // 1-арна: тұрақты сигнал
    win[i][1] = 0.73f;
    // 2-арна: терезеге екі период сыятын синус
    win[i][2] = 0.5f * sinf(4.0f * PI_F * (float)i / (float)WIN);
    // қалған арналар: шуылға ұқсас сигнал
    for (int c = 3; c < N_CH; c++) {
      win[i][c] = nextRand();
    }
  }
}

// ------------------------------------------------- 85 белгіні есептеу
static void extractFeatures() {
  int k = 0;
  for (int c = 0; c < N_CH; c++) {

    // бірінші өтпе: орташа мән, ең үлкен және ең кіші мән
    float sum = 0.0f;
    float mx = win[0][c];
    float mn = win[0][c];
    for (int i = 0; i < WIN; i++) {
      float v = win[i][c];
      sum += v;
      if (v > mx) mx = v;
      if (v < mn) mn = v;
    }
    float mean = sum / (float)WIN;

    // екінші өтпе: дисперсия, еңкею, қиып өту саны
    float sq = 0.0f;
    float num = 0.0f;
    int   cross = 0;
    float prevDev = win[0][c] - mean;
    sq  += prevDev * prevDev;
    num += (0.0f - T_BAR) * prevDev;
    for (int i = 1; i < WIN; i++) {
      float dev = win[i][c] - mean;
      sq  += dev * dev;
      num += ((float)i - T_BAR) * dev;
      if (prevDev * dev < 0.0f) cross++;
      prevDev = dev;
    }

    feat[k++] = mean;                                  // Mean
    feat[k++] = sqrtf(sq / (float)WIN);                // STD
    feat[k++] = mx - mn;                               // Range
    feat[k++] = num / SLOPE_DEN;                       // Slope
    feat[k++] = (float)cross / (float)(WIN - 1);       // ZCR
  }
}

// ------------------------------------------------- көмекші басып шығару
static void line() {
  Serial.println(F("================================================"));
}

void setup() {
  Serial.begin(115200);
  delay(2000);                      // USB CDC порты дайын болуын күту

  line();
  Serial.println(F("БЕЛГІЛЕРДІ ЕСЕПТЕУ УАҚЫТЫН ӨЛШЕУ"));
  Serial.println(F("Жалғас Данил, 10 «В» сынып, BINOM SCHOOL"));
  line();
  Serial.print(F("Тақта   : "));
  Serial.println(ESP.getChipModel());
  Serial.print(F("Жиілік  : "));
  Serial.print(ESP.getCpuFreqMHz());
  Serial.println(F(" МГц"));
  Serial.print(F("Терезе  : "));
  Serial.print(WIN);
  Serial.print(F(" есептеу x "));
  Serial.print(N_CH);
  Serial.println(F(" арна"));
  Serial.println();

  fillWindow();

  // ---------- 1. дұрыстығын тексеру ----------
  extractFeatures();
  line();
  Serial.println(F("1. ДҰРЫСТЫҒЫН ТЕКСЕРУ (0-арна: x = 0,02*i + 0,1)"));
  line();
  const char *nm[N_STAT] = { "Mean ", "STD  ", "Range", "Slope", "ZCR  " };
  // 0-арна үшін формуламен есептелген мәндер (3.1-тармақ):
  //   Mean = a*(N-1)/2 + b,  STD = a*sqrt((N*N-1)/12),  Range = a*(N-1),
  //   Slope = a,             ZCR  = 1/(N-1)
  const float ref[N_STAT] = { 0.5900000f, 0.2886174f, 0.9800000f,
                              0.0200000f, 0.0204082f };
  float worst = 0.0f;
  for (int s = 0; s < N_STAT; s++) {
    float got = feat[s];
    float err = fabsf(got - ref[s]);
    if (err > worst) worst = err;
    Serial.print(F("  "));
    Serial.print(nm[s]);
    Serial.print(F(" = "));
    Serial.print(got, 6);
    Serial.print(F("   формула: "));
    Serial.print(ref[s], 6);
    Serial.print(F("   айырма: "));
    Serial.println(err, 8);
  }
  Serial.print(F("  Ең үлкен айырма: "));
  Serial.println(worst, 8);
  Serial.print(F("  Вектордың өлшемділігі: "));
  Serial.println(N_FEAT);
  Serial.println();

  // ---------- 2. уақытты өлшеу ----------
  extractFeatures();                       // кэшті жылыту
  unsigned long t0 = micros();
  for (int r = 0; r < REPEAT; r++) {
    extractFeatures();
    sink += feat[0];
  }
  unsigned long t1 = micros();

  float perWin = (float)(t1 - t0) / (float)REPEAT;

  line();
  Serial.println(F("2. ЕСЕПТЕУ УАҚЫТЫ"));
  line();
  Serial.print(F("  Қайталау саны        : "));
  Serial.println(REPEAT);
  Serial.print(F("  Жалпы уақыт          : "));
  Serial.print(t1 - t0);
  Serial.println(F(" мкс"));
  Serial.print(F("  Бір терезеге         : "));
  Serial.print(perWin, 1);
  Serial.print(F(" мкс = "));
  Serial.print(perWin / 1000.0f, 3);
  Serial.println(F(" мс"));
  Serial.print(F("  20 мс бюджетінен     : "));
  Serial.print(perWin / 20000.0f * 100.0f, 2);
  Serial.println(F(" %"));
  Serial.println();
  line();
  Serial.println(F("ӨЛШЕУ АЯҚТАЛДЫ"));
  line();
}

void loop() {
  delay(10000);
}
