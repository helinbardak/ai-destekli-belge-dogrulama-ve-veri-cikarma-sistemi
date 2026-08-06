import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  UploadCloud,
  FileText,
  X,
  AlertCircle,
  Loader2,
  Phone,
  ShieldCheck,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Akıllı Belge Yükleme Sistemi" },
      {
        name: "description",
        content:
          "Dahili su hasarı ihbar belgelerinizi güvenle yükleyin. Tapu, kimlik, dilekçe, fatura ve IBAN belgelerinizle hızlı ihbar süreci.",
      },
      { property: "og:title", content: "Akıllı Belge Yükleme Sistemi" },
      {
        property: "og:description",
        content: "Hasar belgelerinizi tek bir alandan güvenle iletin.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const MAX_FILES = 4;
const API_BASE_URL = "http://localhost:8002";
const REQUIRED_DOCS = [
  "Tapu Belgesi",
  "Kimlik Belgesi",
  "İmzalı Beyan Dilekçesi",
  "IBAN / Banka Hesap Bilgisi",
];

const MOCK_CLAIMS = [
  { id: "14184739205831", label: "14184739205831 | Dahili Su Hasarı (Ön İnceleme Bekliyor)" },
  { id: "14159203847162", label: "14159203847162 | Kasko / Trafik Kazası (Eksper Atandı)" },
  { id: "14190384756219", label: "14190384756219 | Yangın Hasarı (Evrak Bekleniyor)" },
];

type AnalyzedFile = {
  id: string;
  originalFile: File;
  status: "analyzing" | "success" | "error";
  docType?: string;
  errorDetail?: string;
};

type ClaimData = {
  file_number?: string;
  claim_type?: string;
  status?: string;
  claim?: { incident_date?: string; insured_name?: string };
  insured?: { full_name?: string; tc_no?: string };
  bank_account?: { iban?: string };
  validation_warnings?: string[];
};

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function Index() {
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [dropdownSelection, setDropdownSelection] = useState<string>("");
  const [files, setFiles] = useState<AnalyzedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [limitError, setLimitError] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [claimData, setClaimData] = useState<ClaimData | null>(null);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const isFull = files.length >= MAX_FILES;

  const handleStartProcess = () => {
    if (!dropdownSelection) return;

    if (dropdownSelection !== "14184739205831") {
      window.alert(
        "Bu hasar türü için otomatik evrak yükleme modülü henüz yapım aşamasındadır. Lütfen Dahili Su (14184739205831) hasar dosyanızı seçerek ilerleyiniz."
      );
      return;
    }
    setActiveClaimId(dropdownSelection);
  };

  const processFile = async (newFile: File, fileId: string) => {
    const formData = new FormData();
    formData.append("file", newFile);

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.status !== "success") {
        throw new Error(data.detail ?? data.message ?? "Belge analizi basarisiz oldu.");
      }
      const documentType = data.result?.document_type?.trim();
      const isActualSuccess =
        data.status === "success" &&
        Boolean(documentType) &&
        REQUIRED_DOCS.includes(documentType);

      if (isActualSuccess) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? { ...f, status: "success", docType: documentType }
              : f
          )
        );
      } else {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? {
                  ...f,
                  status: "error",
                  errorDetail:
                    documentType ?? data.message ?? "Geçersiz veya okunaksız belge",
                }
              : f
          )
        );
      }
    } catch (error) {
      const errorDetail =
        error instanceof Error ? error.message : "Belge yuklenirken bilinmeyen bir hata olustu.";
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, status: "error", errorDetail }
            : f
        )
      );
    }
  };

  const addFiles = useCallback((incoming: FileList | File[]) => {
    setValidationWarnings([]);
    const arr = Array.from(incoming);
    const remaining = MAX_FILES - files.length;

    if (arr.length > remaining) {
      setLimitError(true);
    } else {
      setLimitError(false);
    }

    const toAdd = arr.slice(0, remaining).map((f) => ({
      id: `${f.name}-${f.size}-${Date.now()}-${Math.random()}`,
      originalFile: f,
      status: "analyzing" as const,
    }));

    toAdd.forEach((af) => {
      processFile(af.originalFile, af.id);
    });

    setFiles((prev) => [...prev, ...toAdd]);
  }, [files]);

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (isFull) {
      setLimitError(true);
      return;
    }
    if (e.dataTransfer.files?.length) {
      addFiles(e.dataTransfer.files);
    }
  };

  const onSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      addFiles(e.target.files);
    }
    e.target.value = "";
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
    setLimitError(false);
    setValidationWarnings([]);
  };

  const validatedList = files
    .filter((f) => f.status === "success" && f.docType)
    .map((f) => f.docType!);

  const verifiedCount = files.filter(
    (f) => f.status === "success" && Boolean(f.docType)
  ).length;

  const missingCount = REQUIRED_DOCS.filter(
    (req) =>
      !validatedList.some(
        (val) =>
          val.toLowerCase().includes(req.toLowerCase()) ||
          req.toLowerCase().includes(val.toLowerCase())
      )
  ).length;

  const canSubmit = missingCount === 0 && files.every((f) => f.status === "success");

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setIsSubmitting(true);
    setValidationWarnings([]);

    try {
      const identityFile = files.find((file) => file.docType === REQUIRED_DOCS[1])?.originalFile;
      const deedFile = files.find((file) => file.docType === REQUIRED_DOCS[0])?.originalFile;
      const statementFile = files.find((file) => file.docType === REQUIRED_DOCS[2])?.originalFile;
      const bankFile = files.find((file) => file.docType === REQUIRED_DOCS[3])?.originalFile;

      if (!identityFile || !deedFile || !statementFile || !bankFile) {
        throw new Error("Gerekli belgelerden biri eslestirilemedi.");
      }

      if (!activeClaimId) {
        throw new Error("Hasar dosyası seçilmedi.");
      }

      const formData = new FormData();
      formData.append("identity_file", identityFile);
      formData.append("deed_file", deedFile);
      formData.append("statement_file", statementFile);
      formData.append("bank_file", bankFile);
      formData.append("claim_file_number", activeClaimId);

      const response = await fetch(`${API_BASE_URL}/process-documents`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json();

      if (!response.ok || result.status !== "success") {
        throw new Error(result.message ?? "Belgeler islenemedi.");
      }
      const processedClaim = result.data ?? result;
      const warnings = processedClaim.validation_warnings ?? [];
      setClaimData(processedClaim);

      if (warnings.length > 0) {
        setValidationWarnings(warnings);
        return;
      }

      setSubmitSuccess(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bilinmeyen bir hata olustu.";
      window.alert(`Sisteme baglanirken bir hata olustu: ${message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openPicker = () => {
    if (isFull) {
      setLimitError(true);
      return;
    }
    inputRef.current?.click();
  };

  const buttonLabel = submitSuccess
    ? "Belgeleriniz başarıyla iletildi"
    : isSubmitting
      ? "İşlem tamamlanıyor..."
      : canSubmit
        ? "Belgeleri Gönder"
        : `Belgeleri Gönder (${verifiedCount}/${MAX_FILES} Doğrulandı)`;

  const buttonDisabled = !canSubmit || isSubmitting || submitSuccess;

  if (!activeClaimId) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center p-6 text-slate-800"
        style={{
          backgroundImage: "url('/Screenshot 2026-07-27 205410.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >
        <div className="mt-32 w-full max-w-md rounded-xl bg-white/80 p-8 shadow-xl backdrop-blur-md">
          <div className="space-y-4">
            <label
              htmlFor="claim-select"
              className="mb-1.5 block text-sm font-medium text-slate-800"
            >
              İşlem Yapılacak Dosya
            </label>
            <select
              id="claim-select"
              value={dropdownSelection}
              onChange={(e) => setDropdownSelection(e.target.value)}
              className="w-full cursor-pointer rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-[#0055A5] focus:ring-1 focus:ring-[#0055A5]"
            >
              <option value="" disabled>
                Dosya seçiniz...
              </option>
              {MOCK_CLAIMS.map((claim) => (
                <option key={claim.id} value={claim.id}>
                  {claim.label}
                </option>
              ))}
            </select>
            <button
              onClick={handleStartProcess}
              disabled={!dropdownSelection}
              className="mt-2 flex w-full justify-center rounded-md bg-[#0055A5] px-4 py-2.5 text-sm font-semibold text-white shadow-md transition-colors hover:bg-[#004488] disabled:cursor-not-allowed disabled:opacity-50"
            >
              İşleme Başla
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen text-slate-800"
      style={{
        backgroundImage: "url('/Screenshot 2026-07-27 210152.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundAttachment: "fixed",
      }}
    >
      <header className="border-b border-slate-200/50 bg-white/80 shadow-sm backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0055A5] text-white shadow-md">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="flex items-center text-lg font-semibold leading-tight text-[#0055A5]">
              Evrak Yükleme ve Doğrulama Sistemi
              <span className="ml-3 hidden rounded-md bg-[#0055A5]/10 px-2.5 py-0.5 text-xs font-medium text-[#0055A5] sm:inline-block">
                Dosya: {activeClaimId}
              </span>
            </h1>
            <p className="mt-1 text-xs font-medium text-slate-600">
              Belgelerinizi güvenle iletin, süreciniz hızla başlasın.
            </p>
            </div>
          </div>
          <button
            onClick={() => setActiveClaimId(null)}
            className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 hover:text-[#0055A5]"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Dosya Seçimine Dön</span>
            <span className="sm:hidden">Geri</span>
          </button>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 py-10 lg:grid-cols-2">
        <section className="space-y-6">
          <div className="rounded-lg border border-slate-200 border-l-4 border-l-[#E2001A] bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-base font-semibold text-[#0055A5]">
              Dahili Su Hasarı Anında Yapılması Gereken İşlemler
            </h2>
            <p className="text-sm leading-relaxed text-slate-700">
              Sigortalı konutta tesisat hasarının söz konusu olması durumunda,
              konutun su tesisatının kapatılarak, hasarın önlenmesi
              sağlanmalıdır. Akabinde, ihbar hatlarımız aranarak ihbarda
              bulunulmalıdır.
            </p>

            <h3 className="mt-5 text-sm font-semibold text-[#0055A5]">
              İhbar İşlemleri
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">
              Hasar ihbar işlemlerinizi{" "}
              <span className="inline-flex items-center gap-1 font-semibold text-[#0055A5]">
                <Phone className="h-3.5 w-3.5" />
                0850 724 0850
              </span>{" "}
              numaralı çağrı merkezimiz üzerinden hızlıca gerçekleştirebilirsiniz.
            </p>

            <a
              href="https://www.anadolusigorta.com.tr/hasar-merkezi/hasar-evraklari/oto-disi-hasar"
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-sm font-medium text-[#0055A5] underline underline-offset-4 hover:opacity-80"
            >
              Detaylı bilgi için tıklayınız
            </a>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-base font-semibold text-[#0055A5]">
              Yüklenmesi Gereken Belgeler
            </h2>
            <ul className="space-y-2 text-sm text-slate-700">
              {REQUIRED_DOCS.map((doc) => {
                const isFound = validatedList.some(
                  (type) =>
                    type.toLowerCase().includes(doc.toLowerCase()) ||
                    doc.toLowerCase().includes(type.toLowerCase())
                );

                return (
                  <li key={doc} className="flex items-start gap-2">
                    {isFound ? (
                      <span className="mt-0.5 select-none font-bold text-green-500">✓</span>
                    ) : (
                      <span className="mt-0.5 select-none text-slate-400">-</span>
                    )}
                    <span className={isFound ? "font-medium text-slate-900" : ""}>{doc}</span>
                  </li>
                );
              })}
            </ul>
            <p className="mt-4 text-xs text-slate-500">
              Toplam 4 belgeyi eksiksiz yüklemeniz gerekmektedir.
            </p>
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold text-[#0055A5]">
                Belge Yükleme Alanı
              </h2>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  missingCount === 0
                    ? "bg-[#0055A5]/10 text-[#0055A5]"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {files.length} / {MAX_FILES} belge
              </span>
            </div>

            <div
              onClick={openPicker}
              onDragOver={(e) => {
                e.preventDefault();
                if (!isFull) setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={onDrop}
              className={[
                "group relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-all",
                isFull
                  ? "pointer-events-none cursor-not-allowed border-slate-200 bg-slate-100 opacity-60"
                  : isDragging
                    ? "cursor-pointer border-[#0055A5] bg-[#0055A5]/5"
                    : "cursor-pointer border-slate-300 bg-slate-50 hover:border-[#0055A5] hover:bg-[#0055A5]/5",
              ].join(" ")}
              aria-disabled={isFull}
            >
              <div
                className={`mb-3 flex h-14 w-14 items-center justify-center rounded-full ${
                  isFull ? "bg-slate-200 text-slate-400" : "bg-[#0055A5]/10 text-[#0055A5]"
                }`}
              >
                <UploadCloud className="h-7 w-7" />
              </div>
              <p className="text-sm font-medium text-slate-800">
                {isFull
                  ? "Yükleme limitine ulaştınız"
                  : "Belgelerinizi buraya sürükleyip bırakın"}
              </p>
              {!isFull && (
                <p className="mt-1 text-xs text-slate-500">
                  veya dosya seçmek için tıklayınız (PDF, JPG, PNG)
                </p>
              )}
              <input
                ref={inputRef}
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={onSelect}
                className="hidden"
                disabled={isFull}
              />
            </div>

            {limitError && (
              <div className="mt-3 flex items-center gap-2 text-sm font-medium text-[#E2001A]">
                <AlertCircle className="h-4 w-4" />
                En fazla 4 adet belge yükleyebilirsiniz.
              </div>
            )}

            {files.length > 0 && (
              <ul className="mt-5 space-y-2">
                {files.map((f, idx) => {
                  const isAnalyzing = f.status === "analyzing";
                  const isSuccess = f.status === "success";
                  const isError = f.status === "error";

                  return (
                    <li
                      key={f.id}
                      className={[
                        "flex items-center justify-between gap-3 rounded-md border px-3 py-2.5 transition-colors",
                        isAnalyzing
                          ? "border-[#0055A5] bg-[#0055A5]/5"
                          : isSuccess
                            ? "border-emerald-200 bg-emerald-50/60"
                            : "border-red-200 bg-red-50",
                      ].join(" ")}
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <div
                          className={[
                            "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md",
                            isSuccess
                              ? "bg-emerald-100 text-emerald-600"
                              : isAnalyzing
                                ? "bg-[#0055A5]/10 text-[#0055A5]"
                                : "bg-red-100 text-red-600",
                          ].join(" ")}
                        >
                          {isSuccess ? (
                            <CheckCircle2 className="h-4 w-4" />
                          ) : isAnalyzing ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : isError ? (
                            <AlertCircle className="h-4 w-4" />
                          ) : (
                            <FileText className="h-4 w-4" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-slate-800">
                            {idx + 1}. {f.originalFile.name}
                          </p>
                          <p
                            className={[
                              "text-xs font-medium",
                              isSuccess
                                ? "text-emerald-600"
                                : isAnalyzing
                                  ? "text-[#0055A5]"
                                  : "text-red-600",
                            ].join(" ")}
                          >
                            {isSuccess
                              ? f.docType
                              : isAnalyzing
                                ? "Yapay zeka analiz ediyor..."
                                : f.errorDetail}
                          </p>
                        </div>
                      </div>
                      
                      {!submitSuccess && (
                        <button
                          type="button"
                          onClick={() => removeFile(f.id)}
                          aria-label="Belgeyi kaldır"
                          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-[#E2001A]/10 hover:text-[#E2001A]"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}

            {validationWarnings.length > 0 && (
              <div
                role="alert"
                className="mt-5 rounded-md border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900"
              >
                <p className="flex items-center gap-2 font-semibold">
                  <AlertCircle className="h-[18px] w-[18px] text-orange-600" />
                  Eksik veya uyuşmayan bilgiler var
                </p>
                <p className="mt-1 text-xs leading-relaxed text-orange-800">
                  Lütfen bilgileri kontrol ederek ilgili belgeyi tekrar yükleyiniz.
                </p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-orange-800">
                  {validationWarnings.map((warning, index) => (
                    <li key={`${warning}-${index}`}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
              <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-600">
                <span>{submitSuccess ? "İşlem Tamamlandı" : "Doğrulanan Belgeler"}</span>
                <span className="text-[#0055A5]">
                  {validatedList.length} / {MAX_FILES}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    submitSuccess ? "bg-emerald-500" : validatedList.length === MAX_FILES ? "bg-[#0055A5]" : "bg-[#0055A5]/60"
                  }`}
                  style={{ width: `${(validatedList.length / MAX_FILES) * 100}%` }}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={buttonDisabled}
              className={[
                "mt-6 flex w-full items-center justify-center gap-2 rounded-md px-4 py-3.5 text-sm font-semibold transition-colors",
                submitSuccess
                  ? "bg-emerald-600 text-white"
                  : buttonDisabled
                    ? "cursor-not-allowed bg-slate-200 text-slate-500"
                    : "bg-[#0055A5] text-white hover:bg-[#004488]",
              ].join(" ")}
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {submitSuccess && <CheckCircle2 className="h-4 w-4" />}
              <span>{buttonLabel}</span>
            </button>

            {submitSuccess && (
              <p className="mt-3 text-center text-xs text-emerald-600 font-medium">
                Tüm belgeleriniz başarıyla doğrulanmış ve sistemlerimize iletilmiştir.
              </p>
            )}

            {submitSuccess && claimData && (
              <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-5 text-left">
                <h2 className="border-b-2 border-slate-200 pb-2 text-base font-semibold text-[#0055A5]">
                  HASAR DOSYASI ({claimData.file_number ?? activeClaimId ?? "Numara atanamadi"})
                </h2>

                <div className="mt-4 grid gap-4 text-sm text-slate-700 sm:grid-cols-2">
                  <div className="space-y-2">
                    <p><strong>Hasar Turu:</strong> {claimData.claim_type ?? "Belirtilmedi"}</p>
                    <p><strong>Durum:</strong> <span className="font-semibold text-[#0055A5]">{claimData.status ?? "Belirtilmedi"}</span></p>
                    <p><strong>Hasar Tarihi:</strong> {claimData.claim?.incident_date ?? "Belgeden okunamadi"}</p>
                  </div>
                  <div className="space-y-2">
                    <p><strong>Sigortali:</strong> {claimData.insured?.full_name ?? claimData.claim?.insured_name ?? "Belgeden okunamadi"}</p>
                    <p><strong>T.C. Kimlik No:</strong> {claimData.insured?.tc_no ?? "Belgeden okunamadi"}</p>
                    <p><strong>IBAN:</strong> {claimData.bank_account?.iban ?? "Belgeden okunamadi"}</p>
                  </div>
                </div>

                {!!claimData.validation_warnings?.length && (
                  <div className="mt-5 rounded-md bg-red-100 p-4 text-sm text-red-700">
                    <p className="flex items-center gap-2 font-semibold">
                      <AlertCircle className="h-[18px] w-[18px]" />
                      Sistem Uyarilari (On inceleme gerekiyor)
                    </p>
                    <ul className="mt-2 list-disc space-y-1 pl-5">
                      {claimData.validation_warnings.map((warning, index) => (
                        <li key={`${warning}-${index}`}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          <p className="px-2 text-xs leading-relaxed text-slate-500">
            Belgeleriniz gizlilik esaslarına uygun olarak şifreli bir kanal
            üzerinden işlenmektedir. Yalnızca hasar dosyanızın değerlendirilmesi
            amacıyla kullanılacaktır.
          </p>
        </section>
      </main>
    </div>
  );
}
