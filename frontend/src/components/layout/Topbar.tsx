import { Bars3Icon } from '@heroicons/react/24/outline';
import type { MouseEventHandler } from 'react';

interface TopbarProps {
  onMenuToggle?: MouseEventHandler<HTMLButtonElement>;
}

export default function Topbar({ onMenuToggle }: TopbarProps) {
  return (
    <header className="flex items-center justify-between h-16 px-4 border-b border-gray-200 bg-white shadow-sm md:pl-6">
      <div className="flex items-center space-x-2">
        {/* Mobile menu button */}
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 rounded-md text-neutral-600 hover:bg-gray-100 hover:text-neutral-900 focus:outline-none"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        )}
        <span className="text-lg font-semibold text-brand-dark">EdTech Agent</span>
      </div>
    </header>
  );
}