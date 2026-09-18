import { useCallback, useEffect, useRef, useState } from 'react';
import { getHealthStatus } from '../api';

const MAX_ATTEMPTS = 24;
const RETRY_INTERVAL_MS = 5000;

export default function useBackendHealth() {
  const [status, setStatus] = useState('checking');
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const timeoutRef = useRef(null);

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

      if (attempts >= MAX_ATTEMPTS - 1) {
        setStatus('unavailable');
        setError('Unable to connect to the workforce backend.');
        return false;
      }

      setStatus('checking');
      setError('Backend is starting or temporarily unavailable.');
      return false;
    }
  }, [attempts]);

  const retry = useCallback(() => {
    setAttempts(0);
    setStatus('checking');
    setError('');
  }, []);

  useEffect(() => {
    if (status === 'ready') {
      return undefined;
    }

    let isActive = true;
    if (attempts >= MAX_ATTEMPTS) {
      setStatus('unavailable');
      setError('Unable to connect to the workforce backend.');
      return undefined;
    }

    const runCheck = async () => {
      const ok = await check();
      if (!isActive || ok) return;

      if (attempts >= MAX_ATTEMPTS - 1) {
        return;
      }

      timeoutRef.current = setTimeout(() => {
        if (isActive) {
          setAttempts((previous) => previous + 1);
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
  }, [attempts, check, status]);

  return { status, isReady: status === 'ready', isChecking: status === 'checking', error, retry };
}