import React from 'react';

const Sidebar = () => {
  return (
    <>
      {/* TopNavBar */}
      <header className="h-16 fixed top-0 right-0 left-sidebar-width border-b border-outline-variant dark:border-outline bg-surface dark:bg-surface-dim z-30 flex items-center justify-between px-gutter w-[calc(100%-280px)]">
        <div className="flex items-center gap-4">
          <span className="font-headline-sm text-headline-sm text-on-surface">Risk Management Console</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative w-64">
            <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">search</span>
            <input className="w-full h-10 pl-8 pr-4 bg-surface-container-lowest border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary-fixed rounded text-body-md outline-none transition-all" placeholder="Search orders..." type="text" />
          </div>
          <div className="flex items-center gap-4">
            <button className="text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container-low p-2 rounded-full h-10 w-10 flex items-center justify-center scale-95 active:opacity-80 transition-transform">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>notifications</span>
            </button>
            <button className="text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container-low p-2 rounded-full h-10 w-10 flex items-center justify-center scale-95 active:opacity-80 transition-transform">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>help_outline</span>
            </button>
            <button className="h-10 px-4 bg-primary text-on-primary rounded font-label-md text-label-md hover:opacity-90 transition-opacity">
              Create Case
            </button>
            <div className="h-8 w-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant">
              <img alt="Admin Avatar" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBrehi0LjZ-rOjiNrkfT-1_2FOCgUctKPXqEe9NG-YRa0oqMqM3n3uWOti8XAjINQ5t8HGcPITevnn9_bg7mUAvsJDkISu_J4T9_6I_XvHFoTfCLfCkdEKjNxn98DJb2Vni8MsG-6PztQBjmZEpdFLwMHJyf2UyGmguI54ndTw-U6v0Gqq4-9hdvwdJPDlF9US4ieAnoXSnvr8gvncFH0eXlIxiLCBH7W655tyaBprwO7Me5E03CQ" />
            </div>
          </div>
        </div>
      </header>

      {/* SideNavBar */}
      <nav className="w-sidebar-width h-screen fixed left-0 top-0 border-r border-outline-variant dark:border-outline bg-tertiary-container dark:bg-tertiary-container flex flex-col py-stack-lg z-40">
        <div className="px-6 mb-8 flex items-center gap-3">
          <div className="h-10 w-10 rounded bg-primary flex items-center justify-center text-on-primary font-bold text-lg">
            B
          </div>
          <div>
            <h1 className="font-headline-md text-headline-md text-surface-bright">Boomerang</h1>
            <p className="font-label-sm text-label-sm text-on-secondary-container mt-1 uppercase tracking-wider">Enterprise Admin</p>
          </div>
        </div>
        <ul className="flex flex-col gap-2 mt-4 px-2 w-full font-body-md text-body-md">
          <li className="">
            <a className="flex items-center gap-3 py-3 px-4 rounded w-full text-surface-bright font-bold border-l-2 border-primary-fixed bg-on-primary-fixed-variant transition-colors duration-200 ease-in-out" href="#">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>assignment_late</span>
              Queue
            </a>
          </li>
          <li className="">
            <a className="flex items-center gap-3 py-3 px-4 rounded w-full text-on-secondary-container dark:text-on-secondary-fixed-variant hover:text-surface-bright hover:bg-on-primary-fixed-variant transition-colors transition-all duration-200 ease-in-out pl-4 ml-[2px]" href="#">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>insights</span>
              Analytics
            </a>
          </li>
          <li className="">
            <a className="flex items-center gap-3 py-3 px-4 rounded w-full text-on-secondary-container dark:text-on-secondary-fixed-variant hover:text-surface-bright hover:bg-on-primary-fixed-variant transition-colors transition-all duration-200 ease-in-out pl-4 ml-[2px]" href="#">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>rule</span>
              Rules
            </a>
          </li>
          <li className="mt-auto pt-8">
            <a className="flex items-center gap-3 py-3 px-4 rounded w-full text-on-secondary-container dark:text-on-secondary-fixed-variant hover:text-surface-bright hover:bg-on-primary-fixed-variant transition-colors transition-all duration-200 ease-in-out pl-4 ml-[2px]" href="#">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>settings</span>
              Settings
            </a>
          </li>
        </ul>
      </nav>
    </>
  );
};

export default Sidebar;
