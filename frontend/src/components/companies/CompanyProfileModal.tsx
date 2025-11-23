import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useCompany } from '@/hooks/useCompanies';

interface Props {
  id: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function CompanyProfileModal({ id, isOpen, onClose }: Props) {
  const { data, isLoading, error } = useCompany(id);
  const company = data?.company;
  const sources = data?.sources;

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative w-full max-w-2xl transform overflow-hidden rounded-lg bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-neutral-900">
                  Company profile
                </Dialog.Title>
                {isLoading ? (
                  <div className="py-6 text-center text-gray-500">Loading…</div>
                ) : error ? (
                  <div className="py-6 text-center text-red-600">{error.message}</div>
                ) : company ? (
                  <div className="mt-4 space-y-4">
                    <div>
                      <h4 className="text-xl font-semibold text-neutral-900">{company.name}</h4>
                      {company.website && (
                        <a
                          href={company.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-brand hover:underline"
                        >
                          {company.website.replace(/^https?:\/\//, '')}
                        </a>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2 text-sm">
                      {company.category && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-neutral-800">
                          {company.category}
                        </span>
                      )}
                      {company.region && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-neutral-800">
                          {company.region}
                        </span>
                      )}
                      {company.segment && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-neutral-800">
                          {company.segment}
                        </span>
                      )}
                      {company.size_bucket && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-neutral-800">
                          {company.size_bucket}
                        </span>
                      )}
                      {company.compliance_tags && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-neutral-800">
                          {company.compliance_tags}
                        </span>
                      )}
                    </div>
                    {company.description && (
                      <div>
                        <h5 className="font-medium mt-4">Summary</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.description}</p>
                      </div>
                    )}
                    {company.background && (
                      <div>
                        <h5 className="font-medium mt-4">Background</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.background}</p>
                      </div>
                    )}
                    {company.products && (
                      <div>
                        <h5 className="font-medium mt-4">Products & Services</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.products}</p>
                      </div>
                    )}
                    {company.market_position && (
                      <div>
                        <h5 className="font-medium mt-4">Market Position</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.market_position}</p>
                      </div>
                    )}
                    {company.strengths && (
                      <div>
                        <h5 className="font-medium mt-4">Strengths</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.strengths}</p>
                      </div>
                    )}
                    {company.risks && (
                      <div>
                        <h5 className="font-medium mt-4">Risks</h5>
                        <p className="text-sm text-neutral-700 whitespace-pre-line">{company.risks}</p>
                      </div>
                    )}
                    {sources && sources.length > 0 && (
                      <div>
                        <h5 className="font-medium mt-4">Sources</h5>
                        <ul className="space-y-1 text-sm">
                          {sources.map((src, idx) => (
                            <li key={idx}>
                              <a
                                href={src.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-brand hover:underline"
                              >
                                {src.title || src.url}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : null}
                <button
                  className="absolute top-3 right-3 p-1 text-gray-400 hover:text-gray-600"
                  onClick={onClose}
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}