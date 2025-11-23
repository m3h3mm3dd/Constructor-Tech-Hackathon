import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  BriefcaseIcon,
  Squares2X2Icon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

const navItems = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Research Lab', path: '/lab', icon: BriefcaseIcon },
  { name: 'Compare', path: '/compare', icon: Squares2X2Icon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-60 lg:w-72 flex-col bg-white border-r border-gray-200 shadow-sm">
      <div className="flex items-center justify-center h-16 border-b border-gray-200 px-4">
        <span className="text-xl font-semibold text-brand-dark">EdTech Agent</span>
      </div>
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-4">
          {navItems.map(({ name, path, icon: Icon }) => (
            <li key={name}>
              <NavLink
                to={path}
                end
                className={({ isActive }) =>
                  [
                    'group flex items-center px-3 py-2 rounded-md font-medium text-sm transition-colors',
                    isActive
                      ? 'bg-brand/10 text-brand-dark'
                      : 'text-neutral-700 hover:bg-gray-100 hover:text-neutral-900',
                  ].join(' ')
                }
              >
                <Icon className="h-5 w-5 mr-3 flex-shrink-0" aria-hidden="true" />
                {name}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="p-4 text-xs text-neutral-500 border-t border-gray-200">
        Track 4 – EdTech Competitor Agent
      </div>
    </aside>
  );
}