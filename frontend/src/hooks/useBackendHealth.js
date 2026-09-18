import { useCallback, useEffect, useRef, useState } from 'react';
import { getHealthStatus } from '../api';

const MAX_ATTEMPTS = 24;
const RETRY_INTERVAL_MS = 5000;

export default function useBackendHealth() {
  const [status, setStatus] = useState('checking');
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [retryNonce, setRetryNonce] = useState(0);
  const timeoutRef = useRef(null);
  const attemptsRef = useRef(0);

  const check = useCallback(async () => {
    try {
      const response = await getHealthStatus();
      const health = response.data || {};
      const ready = response.status === 200 && (health.status === 'ok' || health.status === 'OK' || health.status === 'ready');

      if (ready) {
        setStatus('ready');
        setError('');
        return true;
      }

      throw new Error('Backend health response was not ready.');
    } catch (requestError) {
      const responseStatus = requestError?.response?.status;
      if (responseStatus === 404) {
        setStatus('unavailable');
        setError('Health endpoint not found. Check backend deployment.');
        return false;
      }

      if (responseStatus === 403) {
        setStatus('unavailable');
        setError('Backend rejected the health check. Check CORS and deployment configuration.');
        return false;
      }

      if (responseStatus >= 500 && responseStatus !== 502 && responseStatus !== 503) {
        setStatus('unavailable');
        setError(`Backend health check failed with HTTP ${responseStatus}.`);
        return false;
      }

      if (attemptsRef.current >= MAX_ATTEMPTS - 1) {
        setStatus('unavailable');
        setError('Unable to connect to the workforce backend.');
        return false;
      }

      setStatus('checking');
      setError('Backend is starting or temporarily unavailable.');
      return false;
    }
  }, []);

  const retry = useCallback(() => {
    attemptsRef.current = 0;
    setAttempts(0);
    setStatus('checking');
    setError('');
    setRetryNonce((value) => value + 1);
  }, []);

  useEffect(() => {
    if (status === 'ready' || status === 'unavailable') {
      return undefined;
    }

    let isActive = true;
    if (attemptsRef.current >= MAX_ATTEMPTS) {
      setStatus('unavailable');
      setError('Unable to connect to the workforce backend.');
      return undefined;
    }

    const runCheck = async () => {
      const ok = await check();
      if (!isActive || ok) return;

      if (attemptsRef.current >= MAX_ATTEMPTS - 1) {
        return;
      }

      timeoutRef.current = setTimeout(() => {
        if (isActive) {
          attemptsRef.current += 1;
          setAttempts(attemptsRef.current);
        }
      }, RETRY_INTERVAL_MS);
    };

    runCheck();

    return () => {
      isActive = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [attempts, check, retryNonce, status]);

  return { status, isReady: status === 'ready', isChecking: status === 'checking', error, retry };
}