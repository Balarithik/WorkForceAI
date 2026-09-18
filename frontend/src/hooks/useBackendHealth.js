import { useCallback, useEffect, useRef, useState } from 'react';
import { getHealthStatus } from '../api';

const RETRY_INTERVAL_MS = 5000;
const TIMEOUT_MS = 120000;

export default function useBackendHealth() {
  const [status, setStatus] = useState('checking');
  const [isReady, setIsReady] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState('');
  const startedAtRef = useRef(Date.now());
  const intervalRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const checkHealth = useCallback(async () => {
    setIsChecking(true);

    try {
      const response = await getHealthStatus();
      const healthStatus = String(response?.data?.status || '').toLowerCase();

      if (healthStatus === 'ok') {
        setStatus('ready');
        setIsReady(true);
        setError('');
        stopPolling();
        return true;
      }

      const elapsed = Date.now() - startedAtRef.current;
      if (elapsed >= TIMEOUT_MS) {
        setStatus('unavailable');
        setError('Unable to connect to the workforce backend.');
        stopPolling();
        return false;
      }

      setStatus('checking');
      setError('Backend is starting or temporarily unavailable.');
      return false;
    } catch (requestError) {
      const httpStatus = requestError?.response?.status;
      const elapsed = Date.now() - startedAtRef.current;

      if (httpStatus === 404 || httpStatus === 403) {
        setStatus('unavailable');
        setError('The workforce backend configuration is unavailable.');
        stopPolling();
        return false;
      }

      if (elapsed >= TIMEOUT_MS) {
        setStatus('unavailable');
        setError('Unable to connect to the workforce backend.');
        stopPolling();
        return false;
      }

      setStatus('checking');
      setError('Backend is starting or temporarily unavailable.');
      return false;
    } finally {
      setIsChecking(false);
    }
  }, [stopPolling]);

  const retry = useCallback(() => {
    startedAtRef.current = Date.now();
    stopPolling();
    checkHealth();

    intervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startedAtRef.current;
      if (elapsed >= TIMEOUT_MS) {
        setStatus('unavailable');
        setError('Unable to connect to the workforce backend.');
        stopPolling();
        return;
      }
      checkHealth();
    }, RETRY_INTERVAL_MS);
  }, [checkHealth, stopPolling]);

  useEffect(() => {
    retry();
    return () => stopPolling();
  }, [retry, stopPolling]);

  return { status, isReady, isChecking, error, retry };
}
