import { useEffect, useState } from 'react';
import { getEvents } from '../api';
import { Activity } from 'lucide-react';

export default function Events() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    getEvents().then(res => setEvents(res.data.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)))).catch(console.error);
  }, []);

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md border border-gray-100">
      <ul className="divide-y divide-gray-200">
        {events.map((event) => (
          <li key={event.id}>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50 transition">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Activity className="w-5 h-5 text-gray-400 mr-3" />
                  <p className="text-sm font-medium text-indigo-600 truncate">
                    {event.event_type.replace('_', ' ')}
                  </p>
                </div>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className="text-xs text-gray-500">
                    {new Date(event.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex">
                  <p className="flex items-center text-sm text-gray-900">
                    {event.description}
                  </p>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
      {events.length === 0 && <div className="p-6 text-center text-gray-500">No events found.</div>}
    </div>
  );
}
