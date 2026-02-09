import { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { transactions, benefits, type UploadResult, type DetectionResult } from '../lib/api';
import { Upload as UploadIcon, CheckCircle, AlertCircle } from 'lucide-react';

export default function Upload() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [error, setError] = useState('');

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.name.endsWith('.csv')) {
      setFile(droppedFile);
      setError('');
    } else {
      setError('Please drop a CSV file');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file || !token) return;

    setUploading(true);
    setError('');

    try {
      const result = await transactions.upload(file);
      setUploadResult(result);

      // Auto-run detection
      setDetecting(true);
      const detection = await benefits.detect();
      setDetectionResult(detection);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      setDetecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <header className="bg-white border-b px-4 py-4">
        <h1 className="text-xl font-bold">📤 Upload Transactions</h1>
      </header>

      <div className="p-4">
        {!uploadResult ? (
          <>
            {/* Dropzone */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 transition-colors"
            >
              <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">
                Drag & drop your transactions CSV here
              </p>
              <p className="text-sm text-gray-400 mb-4">or</p>
              <label className="cursor-pointer">
                <span className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                  Choose file
                </span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>

            {file && (
              <div className="mt-4 p-4 bg-white rounded-xl">
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : detecting ? 'Detecting benefits...' : 'Upload & Detect'}
                </button>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            <div className="mt-6 p-4 bg-blue-50 rounded-xl">
              <h3 className="font-medium text-blue-900">Supported format</h3>
              <p className="text-sm text-blue-700 mt-1">
                Export from Copilot, Monarch, or similar. CSV should include: date, name, amount, account columns.
              </p>
            </div>
          </>
        ) : (
          /* Results */
          <div className="space-y-4">
            {/* Upload Summary */}
            <div className="bg-white rounded-xl p-4">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-500" />
                <div>
                  <h2 className="font-semibold">Upload Complete</h2>
                  <p className="text-sm text-gray-500">{file?.name}</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-green-50 p-3 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{uploadResult.imported}</p>
                  <p className="text-xs text-green-700">Imported</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-2xl font-bold text-gray-600">{uploadResult.skipped}</p>
                  <p className="text-xs text-gray-500">Skipped</p>
                </div>
                <div className="bg-red-50 p-3 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">{uploadResult.total_errors}</p>
                  <p className="text-xs text-red-700">Errors</p>
                </div>
              </div>
            </div>

            {/* Detection Results */}
            {detectionResult && (
              <div className="bg-white rounded-xl p-4">
                <h2 className="font-semibold mb-3">🔍 Benefits Detected</h2>
                {detectionResult.detected > 0 ? (
                  <>
                    <p className="text-sm text-gray-600 mb-3">
                      Found {detectionResult.detected} benefit credits across {detectionResult.cards_checked} cards
                    </p>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {detectionResult.benefits.slice(0, 10).map((b, i) => (
                        <div key={i} className="flex justify-between items-center p-2 bg-green-50 rounded-lg text-sm">
                          <div>
                            <p className="font-medium">{b.benefit}</p>
                            <p className="text-xs text-gray-500">{b.card}</p>
                          </div>
                          <span className="font-semibold text-green-600">${b.amount.toFixed(2)}</span>
                        </div>
                      ))}
                      {detectionResult.benefits.length > 10 && (
                        <p className="text-xs text-gray-400 text-center">
                          +{detectionResult.benefits.length - 10} more
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-gray-500">No new benefits detected in this upload.</p>
                )}
              </div>
            )}

            <button
              onClick={() => navigate('/')}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              View Dashboard
            </button>

            <button
              onClick={() => {
                setFile(null);
                setUploadResult(null);
                setDetectionResult(null);
              }}
              className="w-full py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Upload Another File
            </button>
          </div>
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-2 flex justify-around">
        <Link to="/" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">📊</span>
          <span className="text-xs mt-1">Dashboard</span>
        </Link>
        <Link to="/upload" className="flex flex-col items-center py-2 px-4 text-blue-600">
          <span className="text-xl">📤</span>
          <span className="text-xs mt-1">Upload</span>
        </Link>
        <Link to="/cards" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">💳</span>
          <span className="text-xs mt-1">Cards</span>
        </Link>
      </nav>
    </div>
  );
}
