import { ApplicationRef, NgModule } from '@angular/core';
import { BrowserModule }  from '@angular/platform-browser';
import { HttpModule, XSRFStrategy, CookieXSRFStrategy } from '@angular/http';
import { MaterialModule } from '@angular/material';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { AssociateEmailModule } from './associate-email/associate-email.module'
import { AuthModule } from './auth-github/auth.module';
import { INITIAL_DATA_CACHE, loadInitialDataCache } from './initial-data-cache';
import { PageNotFoundComponent } from './not-found.component';
import { RepositoryModule } from './repository/repository.module';

// Stubbing this out as a factory to make AoT happy.
// https://github.com/angular/angular/issues/14200
export function xsrfFactory() {
    return new CookieXSRFStrategy('csrftoken', 'X-CSRFToken')
}

@NgModule({
    imports: [
        BrowserModule,
        HttpModule,
        MaterialModule,
        // Order of the following modules is important because
        // they have Routers within them.
        AssociateEmailModule,
        AuthModule,
        RepositoryModule,
        AppRoutingModule,
    ],
    declarations: [
        AppComponent,
        PageNotFoundComponent,
    ],
    providers: [
        {
            // Ensure CSRF tokens are included in headers during API requests.
            provide: XSRFStrategy,
            useFactory: xsrfFactory,
        },
        {
            // Inject serverside data if we got it.
            provide: INITIAL_DATA_CACHE,
            useFactory: loadInitialDataCache
        },
    ],
    entryComponents: [
        AppComponent,
    ],
})
export class AppModule {
    ngDoBootstrap(appRef: ApplicationRef) {
        appRef.bootstrap(AppComponent);
    }
}
