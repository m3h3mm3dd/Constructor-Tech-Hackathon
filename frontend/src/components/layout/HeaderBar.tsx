import { useNavigate, useLocation } from 'react-router-dom';
import { RocketLaunchIcon, Squares2X2Icon } from '@heroicons/react/24/outline';

export default function HeaderBar() {
  const navigate = useNavigate();
  const location = useLocation();

  const onMissionsClick = () => {
    if (location.pathname !== '/dashboard') {
      navigate('/dashboard');
    }
  };

  return (
    <header className="w-full bg-[#f6f7fb]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-full bg-neutral-900 text-white flex items-center justify-center shadow-lg shadow-purple-200/50">
            <RocketLaunchIcon className="h-6 w-6" aria-hidden="true" />
          </div>
          <span className="text-lg font-semibold tracking-tight">SCOUT</span>
          <button
            type="button"
            onClick={onMissionsClick}
            className="ml-3 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-neutral-200 text-sm font-medium shadow-sm hover:shadow transition"
          >
            <Squares2X2Icon className="h-5 w-5 text-neutral-700" />
            Missions
          </button>
        </div>
        <div className="px-3 py-1 rounded-full text-xs font-semibold bg-white border border-neutral-200 text-neutral-500 uppercase tracking-wide">
          Market Intelligence v2.0
        </div>
      </div>
    </header>
  );
}
